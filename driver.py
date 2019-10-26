#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Driver script"""

__author__ = 'Pedro Larroy'
__version__ = '0.1'

import os
import sys
from subprocess import check_call
import argparse
import logging
import logging.config
import importlib
import yaml
from util import *

def config_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Drive infrastructure and training with a simple commandline tool.",
        epilog="""
Example:
./driver.py -f create_inventory bert
""")
    parser.add_argument('config', nargs=1, help='config file')
    return parser


def execute(config: str) -> None:
    with open(config, 'r') as fh:
        config = yaml.load(fh, Loader=yaml.SafeLoader)
    sys.path.append(config['basedir'])
    logging.info("Looking for '%s' method in module %s in %s",
                 config['pyfunction'], config['pymodule'], config['basedir'])
    mod = importlib.import_module(config['pymodule'], config['basedir'])
    with remember_cwd():
        os.chdir(config['basedir'])
        getattr(mod, config['pyfunction'])(config)


def main():
    config_logging()
    parser = config_argparse()
    args = parser.parse_args()
    if not len(args.config) == 1:
        logging.error("specify a config file")
        parser.print_help()
        return 1
    execute(args.config[0])
    return 0

if __name__ == '__main__':
    sys.exit(main())


