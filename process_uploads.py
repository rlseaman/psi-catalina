#! /usr/bin/env python3
import sys

import os
import os.path
import itertools
from bs4 import BeautifulSoup

def main(argv=None):
    if argv == None:
        argv = sys.argv

    dirname = argv[1]

    if semaphore_exists(dirname):
        process_uploads(dirname, '')

        #update_archive(archive_dir, changes)

    return 0

def update_archive(archive_dir, changes):
    pass

def semaphore_exists(dirname):
    return True

def process_uploads(dirname, archive_dir):
    #for each label in label directory:
    #   parse the label, yielding product id and file name
    #   move label and file to destination directory
    #   add an entry to the change list for that product
    files = [x for x in find_files(dirname)]
    labeldict = parselabels(dirname, files)

    label_files = labeldict.keys()
    data_files = [get_sibling(l, labeldict.get(l, {})['file_name']) for l in labeldict.keys()]

    unaccounted = [f for f in files if f not in label_files and f not in data_files]

    if unaccounted:
       raise (Exception('Some files were not recognized as products: ' + ','.join(unaccounted)))


    # move the files to the archive directory
    for f in label_files.keys():
        l = label_files[f]
        collection_id = l['collection_id']
        dest_directory = os.path.join(dir_name, collection_id)
        # move file


    lids = [(label_files[f]['collection_id'], label_files[f]['logical_id']) for f in label_files.keys()]

    collection_produts = {}
    for collection_id, logical_id in lids:
        collection_products.setdefault(collectionId, []).append(logical_id)

    # update the collections
    #    increment the version number
    #    add the products in the change list to the collection inventory

    # update the bundle
    #    increment the version number

def parselabels(dirname, files):
    # find all .xml files
    xmlfiles = [x for x in files if x.endswith('.xml')]
    labelpairs = [(x, extractlabel(parselabel(x))) for x in xmlfiles]
    return dict([(x, l) for x, l in labelpairs if l])


def find_files(dirname):
    filelists = [[os.path.join(subdir,f) for f in files] for subdir, _, files in os.walk(dirname)]
    return itertools.chain.from_iterable(filelists)

def extractlabel(label):
    p = label.Product_Observational
    if p:
        result = {}

        i = p.Identification_Area
        lid = i.logical_identifier.string
        result['logical_id'] = lid
        result['collection_id'] = lid.split(':')[4]

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

if __name__ == '__main__':
    sys.exit(main())