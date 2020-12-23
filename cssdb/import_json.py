#! /usr/bin/env python3

import sys

import cssdb
import json

def main(argv=None):
    if argv is None:
        argv = sys.argv

    file_name = argv[1]
    extracted = json.load(file_name)
    cssdb.write_directory(extracted, file_name)

if __name__ == '__main__':
    sys.exit(main())
