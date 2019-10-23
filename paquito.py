#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paquito
=======

A simple AMI building tool.

Will launch an instance and provision with Ansible playbooks and create an AMI out of it.

"""
import os
import sys
import subprocess
import glob
import logging
import argparse
import getpass
import boto3
from os.path import expanduser
from subprocess import check_call
import botocore
import yaml
import re
from util import *
import itertools

def group_user_data(xs):
    """Group a flat list of [file, mime, file, mime] into
    [[file, mime], [file,mime]]"""
    assert len(xs) % 2 == 0
    q = deque(xs)
    res = []
    while q:
        res.append( (q.popleft(), q.popleft()) )
    return res


def flatten(xs):
    return list(itertools.chain.from_iterable(xs))


def parse_args(**kwargs):
    parser = argparse.ArgumentParser(description="Paquito AMI packer")
    parser.add_argument('-n', '--instance-name', default=kwargs.get('instance-name',
                        "{}-{}".format('paquito', getpass.getuser())))
    parser.add_argument('-i', '--instance-type', default=kwargs.get('instance-type'))
    parser.add_argument('--ubuntu', default=kwargs.get('ubuntu'))
    parser.add_argument('-u', '--username',
                        default=kwargs.get('username', getpass.getuser()))
    ssh_key = kwargs.get('ssh-key', os.path.join(expanduser("~"),".ssh","id_rsa.pub"))
    parser.add_argument('--ssh-key-file', default=ssh_key)
    parser.add_argument('--ssh-key-name', default="ssh_{}_key".format(getpass.getuser()))
    parser.add_argument('-a', '--ami', default=kwargs.get('ami'))
    parser.add_argument('-p', '--playbook', default=kwargs.get('playbook'))
    parser.add_argument('-m', '--image-name', default=kwargs.get('image-name'))
    parser.add_argument('--user-data', nargs="*")
    parser.add_argument('--keep-instance',
                        help="Keep instance on to diagnose problems",
                        action='store_true')
    parser.add_argument('-d', '--image-description', default=kwargs.get('image-description'))
    parser.add_argument('rest', nargs='*')
    args = parser.parse_args()
    return args


def fill_args_interactive(args, current_region):
    if not args.instance_name:
        args.instance_name = input("instance_name: ")
    if not args.instance_type:
        args.instance_type = input("instance_type (https://www.ec2instances.info): ")

    if not args.ssh_key_file:
        args.ssh_key_file = input("(public) ssh_key_file: ")
    assert os.path.isfile(args.ssh_key_file)

    if not args.ubuntu:
        args.ubuntu = input("ubuntu release (or specific 'ami'): ")

    if args.ubuntu.startswith('ami') or args.ubuntu.startswith('aki'):
        args.ami = ubuntu
        args.ubuntu = None
    else:
        args.ami = get_ubuntu_ami(current_region, args.ubuntu)
        logging.info("Automatic Ubuntu ami selection based on region %s and release %s -> AMI id: %s",
                     current_region, args.ubuntu, args.ami)
    if not args.username:
        args.username = input("user name: ")

    if not args.playbook:
        args.playbook = input("Ansible playbook: ")


def validate_args(args):
    assert args.ami
    assert args.instance_type
    assert args.playbook and os.path.isfile(args.playbook)
    assert args.ssh_key_file and os.path.isfile(args.ssh_key_file)


def main():
    # Launch a new instance each time by removing the state, otherwise tf will destroy the existing
    # one first
    def script_name() -> str:
        return os.path.split(sys.argv[0])[1]

    config_logging()

    launch_template = dict()
    launch_template_file = os.getenv('PAQUITO_TEMPLATE', 'ami_launch_template.yml')
    if os.path.exists(launch_template_file):
        with open(launch_template_file, 'r') as f:
            launch_template = yaml.load(f, Loader=yaml.SafeLoader)

    args = parse_args(**launch_template)
    if args.user_data:
        args.user_data = group_user_data(args.user_data)
    else:
        args.user_data = launch_template['user-data']

    boto3_session = boto3.session.Session()
    current_region = boto3_session.region_name

    fill_args_interactive(args, current_region)
    validate_args(args)

    ec2_resource = boto3.resource('ec2')
    ec2_client = boto3.client('ec2')
    aws_account = boto3.client('sts').get_caller_identity()['Account']

    logging.info("""

    AWS Account: %s
    Instance type: %s
    Region: %s
    Base AMI: %s
    Playbook: %s
    User Data: %s

    """, aws_account, args.instance_type, current_region, args.ami, args.playbook, args.user_data)

    try:
        logging.info("Creating security groups")
        security_groups = create_ssh_anywhere_sg(ec2_client, ec2_resource)
    except botocore.exceptions.ClientError as e:
        logging.info("Continuing: Security group might already exist or be used by a running instance")
        security_groups = ['ssh_anywhere']


    try:
        ec2_client.import_key_pair(KeyName=args.ssh_key_name, PublicKeyMaterial=read_file(args.ssh_key_file))
    except botocore.exceptions.ClientError as e:
        logging.info("Continuing: Key pair '%s' might already exist", args.ssh_key_name)

    logging.info("creating instances")
    instances = create_instances(
        ec2_resource,
        args.instance_name,
        args.instance_type,
        args.ssh_key_name,
        args.ami,
        security_groups,
        args.user_data,
        launch_template.get('CreateInstanceArgs', {}))

    wait_for_instances(instances)
    hosts = [i.public_dns_name for i in instances]
    try:
        for host in hosts:
            logging.info("Waiting for host {}".format(host))
            wait_port_open(host, 22, 300)
            ansible_provision_host(host, args.username, args.playbook)
        logging.info("All done, the following hosts are now available: %s", hosts)


        logging.info("Creating AMI %s from instance %s...", hosts[0], image_name)
        create_image_args = dict(
            BlockDeviceMappings = launch_template['CreateInstanceArgs']['BlockDeviceMappings']
        )
        create_image(ec2_client, hosts[0], image_name, image_description, **create_image_args)
        logging.info("AMI creationg complete.")
    finally:
        if not args.keep_instance:
            logging.info("Terminate instances")
            for instance in instances:
                instance.terminate()
    return 0

if __name__ == '__main__':
    sys.exit(main())

