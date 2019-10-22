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
from util import *

def config_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="", epilog="")
    parser.add_argument('bdir', nargs='?', help='directory with benchmark metadata')
    parser.add_argument('-m', type=str, default='prepare',
        help='module to call')
    parser.add_argument('-f', type=str, default='prepare',
        help='function to call')
    return parser


def execute(bdir: str, m: str='prepare', f: str='prepare') -> None:
    sys.path.append(bdir)
    j = os.path.join
    logging.info("Looking for '%s' method in module in %s", f, bdir)
    mod = importlib.import_module(m, bdir)
    with remember_cwd():
        os.chdir(bdir)
        logging.info(f" = {m}.{f} = ")
        getattr(mod, f)()


def main():
    config_logging()
    logging.info("MXNet Mask RCNN benchmark driver")
    parser = config_argparse()
    args = parser.parse_args()
    if args.bdir:
        if os.path.exists(args.bdir):
            logging.info("Using benchmark metadata folder: %s", args.bdir)
        else:
            raise RuntimeError(f"benchmark metadata '{args.bdir}' must be a directory")
    else:
        raise RuntimeError("Not implemented")

    execute(args.bdir, args.m, args.f)
    return 0

if __name__ == '__main__':
    sys.exit(main())


