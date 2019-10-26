#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Description"""

__author__ = 'Pedro Larroy'
__version__ = '0.1'

import os
import sys
import subprocess
import argparse
from itertools import chain

def main():
    parser = argparse.ArgumentParser(description="""Get abspath of file optionally quoted for rsync""", epilog="")
    parser.add_argument("-e", "--escape",
        help="escape special characters",
        action='store_true')
    parser.add_argument("command",
                help="command to run in the container",
                nargs='*', action='append', type=str)
    args = parser.parse_args()
    command = list(chain(*args.command))
    for p in command:
        print(os.path.abspath(p))
    #print(command)
    return 1

if __name__ == '__main__':
    sys.exit(main())

