#! /usr/bin/env python3
import sys

import os
import os.path
import itertools
from bs4 import BeautifulSoup

IGNORE_FILES=['signature.md5', '.autoxfer']

def main(argv=None):
    if argv == None:
        argv = sys.argv

    dirname = argv[1]
    process_directory(dirname)

    return 0

def process_directory(dirname)
    files = [x for x in find_files(dirname)]
    if semaphore_exists(dirname, files):
        process_uploads(dirname, files,'')

        #update_archive(archive_dir, changes)

def update_archive(archive_dir, changes):
    pass

def semaphore_exists(dirname, files):
    return os.path.join(dirname, '.autoxfer') in files

def process_uploads(dirname, files, archive_dir):
    #for each label in label directory:
    #   parse the label, yielding product id and file name
    #   move label and file to destination directory
    #   add an entry to the change list for that product
    labels = parselabels(dirname, files)

    label_files = [l['label_file_name'] for l in labels]
    data_files = [l['file_name'] for l in labels]

    unaccounted = [f for f in files if f not in label_files and f not in data_files and not ignore(f)]

    if unaccounted:
       raise (Exception('Some files were not recognized as products: ' + ','.join(unaccounted)))


    # move the files to the archive directory
    for l in labels:
        collection_id = l['collection_id']
        dest_directory = os.path.join(dirname, collection_id)
        # move file


    lids = [(l['collection_id'], l['logical_id']) for l in labels]


    collection_products = {}
    for collection_id, logical_id in lids:
        collection_products.setdefault(collection_id, []).append(logical_id)

    lidvids = [l['logical_id'] + "::" + l['version_id'] for l in labels]
    collection_inventory = ['P,' + lidvid for lidvid in lidvids]

    print ("\r\n".join(collection_inventory))


    # update the collections
    #    increment the version number
    #    add the products in the change list to the collection inventory
    #    need collection template
    

    # update the bundle
    #    increment the version number
    #    need bundle template

def parselabels(dirname, files):
    # find all .xml files
    xmlfiles = [x for x in files if x.endswith('.xml')]
    return [extractlabel(parselabel(x), x) for x in xmlfiles]

def find_files(dirname):
    filelists = [[os.path.join(subdir,f) for f in files] for subdir, _, files in os.walk(dirname)]
    return itertools.chain.from_iterable(filelists)

def extractlabel(label, labelfilename):
    p = label.Product_Observational
    if p:
        result = {}
        result['label_file_name'] = labelfilename

        i = p.Identification_Area
        lid = i.logical_identifier.string
        result['logical_id'] = lid
        result['collection_id'] = lid.split(':')[4]
        result['version_id'] = i.version_id.string

        f = p.File_Area_Observational
        result ['file_name'] = f.File.file_name.string
        
        
        return result
    else:
        return None

def parselabel(filename):
    with open(filename) as f:
        return BeautifulSoup(f, 'lxml-xml')

def get_sibling(fq_file, f):
    dirname = os.path.dirname(fq_file)
    return os.path.join(dirname, f)

def ignore(file):
    return any((file.endswith(name) for name in IGNORE_FILES))


if __name__ == '__main__':
    sys.exit(main())