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


def parse_args():
    with open('ami_launch_template.yml', 'r') as f:
        launch_template = yaml.load(f)
    parser = argparse.ArgumentParser(description="Paquito AMI packer")
    parser.add_argument('-n', '--instance-name', default=launch_template.get('instance-name',
                        "{}-{}".format('paquito', getpass.getuser())))
    parser.add_argument('-i', '--instance-type', default=launch_template.get('instance-type'))
    parser.add_argument('--ubuntu', default=launch_template.get('ubuntu'))
    parser.add_argument('-u', '--username',
                        default=launch_template.get('username', getpass.getuser()))
    ssh_key = launch_template.get('ssh-key', os.path.join(expanduser("~"),".ssh","id_rsa.pub"))
    parser.add_argument('--ssh-key-file', default=ssh_key)
    parser.add_argument('--ssh-key-name', default="ssh_{}_key".format(getpass.getuser()))
    parser.add_argument('-a', '--ami', default=launch_template.get('ami'))
    parser.add_argument('-p', '--playbook', default=launch_template.get('playbook'))
    parser.add_argument('-m', '--image-name', default=launch_template.get('image-name'))
    parser.add_argument('-d', '--image-description', default=launch_template.get('image-description'))
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

    args = parse_args()

    boto3_session = boto3.session.Session()
    current_region = boto3_session.region_name
    logging.info("AWS Region is %s", current_region)

    fill_args_interactive(args, current_region)
    validate_args(args)

    ec2_resource = boto3.resource('ec2')
    ec2_client = boto3.client('ec2')

    loggin.info("""
    Instance type: %s
    Base AMI: %s
    Playbook: %s
    """, args.instance_type, args.ami, args.playbook)

    try:
        logging.info("Creating security groups")
        security_groups = create_ssh_anywhere_sg(ec2_client, ec2_resource)
    except botocore.exceptions.ClientError as e:
        logging.exception("Continuing: Security group might already exist or be used by a running instance")
        security_groups = ['ssh_anywhere']


    try:
        ec2_client.import_key_pair(KeyName=args.ssh_key_name, PublicKeyMaterial=read_file(args.ssh_key_file))
    except botocore.exceptions.ClientError as e:
        logging.exception("Continuing: Key pair might already exist")

    logging.info("creating instances")
    with open('launch_template.yml', 'r') as f:
        launch_template = yaml.load(f)
    instances = create_instances(
        ec2_resource,
        instance_name,
        instance_type,
        args.ssh_key_name,
        ami,
        security_groups,
        launch_template.get('CreateInstanceArgs', {}))

    wait_for_instances(instances)
    hosts = [i.public_dns_name for i in instances]
    for host in hosts:
        logging.info("Waiting for host {}".format(host))
        wait_port_open(host, 22, 300)
        ansible_provision_host(host, username, args.playbook)
    logging.info("All done, the following hosts are now available: %s", hosts)


    logging.info("Creating AMI %s from instance %s...", hosts[0], image_name)
    create_image_args = dict(
        BlockDeviceMappings = launch_template['CreateInstanceArgs']['BlockDeviceMappings']
    )
    create_image(ec2_client, hosts[0], image_name, image_description, **create_image_args)
    logging.info("AMI creationg complete.")
    return 0

if __name__ == '__main__':
    sys.exit(main())

