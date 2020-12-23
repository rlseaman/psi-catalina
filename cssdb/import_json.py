#! /usr/bin/env python3

import sys

import cssdb
import json
import argparse

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Parse a CSS JSON file and write it to the database')
    parser.add_argument('--filename', help='The file name for the JSON file', required=True)
    args = parser.parse_args()

    extracted = json.load(args.filename)
    cssdb.write_directory(extracted, args.filename)

if __name__ == '__main__':
    sys.exit(main())
