#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    parser = argparse.ArgumentParser(description="launcher")
    parser.add_argument('-n', '--instance-name', default=launch_template.get('instance-name', "{}-{}".format('worker', getpass.getuser())))
    parser.add_argument('-i', '--instance-type', default=launch_template['instance-type'])
    parser.add_argument('--ubuntu', default=launch_template.get('ubuntu'))
    parser.add_argument('-u', '--username',
                        default=launch_template.get('username', getpass.getuser()))
    ssh_key = launch_template.get('ssh-key', os.path.join(expanduser("~"),".ssh","id_rsa.pub"))
    parser.add_argument('--ssh-key-file', default=ssh_key)
    parser.add_argument('--ssh-key-name', default="ssh_{}_key".format(getpass.getuser()))
    parser.add_argument('-a', '--ami', default=launch_template['ami'])
    parser.add_argument('rest', nargs='*')
    args = parser.parse_args()
    return args


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

    instance_name = input("instance_name [{}]: ".format(args.instance_name))
    if not instance_name:
        instance_name = args.instance_name

    instance_type = input("instance_type (https://www.ec2instances.info) [{}]: ".format(args.instance_type))
    if not instance_type:
        instance_type = args.instance_type

    ssh_key_file = input("(public) ssh_key_file [{}]: ".format(args.ssh_key_file))
    if not ssh_key_file:
        ssh_key_file = args.ssh_key_file
    assert os.path.isfile(ssh_key_file)

    ubuntu = input("ubuntu release (or specific 'ami') [{}]: ".format(args.ubuntu))
    if not ubuntu:
        ubuntu = args.ubuntu

    if ubuntu.startswith('ami') or ubuntu.startswith('aki'):
        args.ami = ubuntu
        ubuntu = None

    if not ubuntu:
        ami = input("ami [{}]: ".format(args.ami))
        if not ami:
            ami = args.ami
    else:
        ami = get_ubuntu_ami(current_region, ubuntu)
        logging.info("Automatic Ubuntu ami selection based on region %s and release %s -> AMI id: %s",
                     current_region, ubuntu, ami)

    username = input("user name [{}]: ".format(args.username))
    if not username:
        username = args.username

    ec2_resource = boto3.resource('ec2')
    ec2_client = boto3.client('ec2')

    try:
        logging.info("Creating security groups")
        security_groups = create_ssh_anywhere_sg(ec2_client, ec2_resource)
    except botocore.exceptions.ClientError as e:
        logging.exception("Continuing: Security group might already exist or be used by a running instance")
        security_groups = ['ssh_anywhere']


    try:
        ec2_client.import_key_pair(KeyName=args.ssh_key_name, PublicKeyMaterial=read_file(ssh_key_file))
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
        provision(host, username)

    logging.info("All done, the following hosts are now available: %s", hosts)
    return 0

if __name__ == '__main__':
    sys.exit(main())

