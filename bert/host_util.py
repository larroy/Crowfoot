#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import sys
import urllib.request
import re
from subprocess import check_call

def set_hostname() -> None:
    ip = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/public-ipv4').read().decode()
    ip = ip.replace('.', '-')
    with open('/etc/hostname', 'w+') as fh:
        fh.write(ip)
        fh.write('\n')
    check_call(['hostname', '-F', '/etc/hostname'])


def config_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('f', nargs='+', type=str, default='list_f',
        help='function to call')
    return parser


def main():
    parser = config_argparse()
    args = parser.parse_args()
    for f in args.f:
        globals()[f]()
    return 0

if __name__ == '__main__':
    sys.exit(main())


