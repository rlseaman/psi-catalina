#! /usr/bin/env python3

import sys

import cssdb
import json
import argparse
import logging

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Parse a CSS JSON file and write it to the database')
    parser.add_argument('--filename', help='The file name for the JSON file', required=True)
    parser.add_argument('--verbose', help='Includes additonal log information if true', action="store_true")
    args = parser.parse_args()

    loglevel = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=loglevel,format='%(asctime)s|%(levelname)s|%(message)s')

    logging.info("Processing: " + args.filename)

    with (open(args.filename)) as f:
        extracted = json.load(f)
        cssdb.write_directory(extracted, args.filename)

if __name__ == '__main__':
    sys.exit(main())
