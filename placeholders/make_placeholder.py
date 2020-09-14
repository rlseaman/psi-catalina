#! /usr/bin/env python3

import jinja2
import sys

TEMPLATE=jinja2.Template(open('placeholder.xml.txt').read())

def main():
    for line in sys.stdin:
        filename = line.strip()
        labelfilename = build_labelfilename(filename)
        with open("out/" + labelfilename, 'w') as labelfile:
            labelfile.write(TEMPLATE.render(logical_id=build_lid(filename), file_name=filename))

def build_lid(product_id):
    return 'urn:nasa:pds:catalina:data:' + product_id

def build_labelfilename(filename):
    return filename.replace('.fz', '').replace('.gz', '') + '.xml'

if __name__ == '__main__':
    main()