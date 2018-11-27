#! /usr/bin/env python3
import sys

import os
import os.path
import itertools
from bs4 import BeautifulSoup

INSTRUMENTS=['G96']
IGNORE_FILES=['signature.md5', '.autoxfer']
IGNORE_DATES=['pds4']
DEST_BASE='.'

def main(argv=None):
    if argv == None:
        argv = sys.argv

    basedir = argv[1]

    # if lockfile exists
    #   create lockfile
    #   process everything
    #   finally
    #      delete lockfile

    lidvids = []
    for instrument in INSTRUMENTS:
        lidvids.extend(process_inst_directory(basedir, instrument))

    collection_lids = index(lidvids, extract_collection_id)

    for collection_id in collection_lids.keys():
        collection_lidvids = collection_lids[collection_id]
        collection_path = ''
        major, minor = get_last_version_number(collection_id, collection_path)
        inventory = read_inventory(major, minor,collection_id, collection_path)
        inventory.extend(['P,' + x for x in collection_lidvids])
        newmajor = major + 1
        newminor = 0
        write_inventory(newmajor, newminor, collection_id, collection_path)
        write_collection(newmajor, newminor, collection_path, collection_path)
    
    # update the bundle - may be able to skip be referencing only collection lids
    #    increment the version number
    #    need bundle template    

    # rsync updates to archive server

    return 0

def get_last_version_number(collection_id, collection_path):
    return (0,0)

def read_inventory(major, minor, collection_id, collection_path):
    return []

def write_inventory(major, minor, collection_id, collection_path):
    pass

def write_collection(major, minor, collection_id, collection_path):
    pass

def process_inst_directory(basedir, instrument):
    instdir = os.path.join(basedir, instrument)

    years = [x.name for x in os.scandir(instdir) if x.is_dir()]

    result = []
    for year in years:
        yeardir = os.path.join(instdir, year)
        result.extend(process_year_directory(yeardir, instrument, year))
    return result

def process_year_directory(yeardir, instrument, year):
    dates = [x.name for x in os.scandir(yeardir) if x.is_dir() and x not in IGNORE_DATES]
    result = []
    for date in dates:
        datadir = os.path.join(yeardir, date)
        labeldir = os.path.join(yeardir, "pds4", date)
        print (datadir, labeldir)
        result.extend(process_data(datadir, labeldir, instrument, year, date))
    return result    



def process_data(datadir, labeldir, instrument, year, date):
    if semaphore_exists(datadir) and semaphore_exists(labeldir):
        return process_uploads(datadir, labeldir, instrument, year, date)
    return []
    #update_archive(archive_dir, changes)

def update_archive(archive_dir, changes):
    pass

def semaphore_exists(dirname):
    semaphore_file = os.path.join(dirname, '.autoxfer')
    return os.path.exists(semaphore_file)

def process_uploads(datadir, labeldir, instrument, year, date):
    print (labeldir)
    #for each label in label directory:
    #   parse the label, yielding product id and file name
    #   move label and file to destination directory
    #   add an entry to the change list for that product
    print ("Directories", datadir, labeldir)
    files = [os.path.join(labeldir, x.name) for x in os.scandir(labeldir) if x.name.endswith('.xml')]
    labels = parselabels(files)

    #label_file_names = [l['label_file_name'] for l in labels]
    #data_file_names = [l['file_name'] for l in labels]
    #unaccounted = [f for f in files if f not in label_file_names and f not in data_file_names and not ignore(f)]
    #if unaccounted:
    #   raise (Exception('Some files were not recognized as products: ' + ','.join(unaccounted)))
    

    # move the files to the archive directory
    for l in labels:
        collection_id = l['collection_id']
        dest_directory = os.path.join(DEST_BASE, collection_id, instrument, year, date)
        print (dest_directory)
        #os.makedirs(dest_directory, exist_ok=True)
        
        src_data = os.path.join(datadir, l['file_name'])
        dest_data = os.path.join(dest_directory, l['file_name'])
        print(src_data, dest_data)
        #os.rename(src_data, dest_data)
        
        src_label = os.path.join(labeldir, l['label_file_name'])
        dest_label = os.path.join(dest_directory, l['label_file_name'])
        print(src_label, dest_label)
        #os.rename(src_label, dest_label)

    lids = [(l['collection_id'], l['logical_id']) for l in labels]

    collection_products = {}
    for collection_id, logical_id in lids:
        collection_products.setdefault(collection_id, []).append(logical_id)

    lidvids = [l['logical_id'] + "::" + l['version_id'] for l in labels]

    return lidvids




def parselabels(files):
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
        result['label_file_name'] = os.path.basename(labelfilename)

        i = p.Identification_Area
        lid = i.logical_identifier.string
        result['logical_id'] = lid
        result['collection_id'] = extract_collection_id(lid)
        result['version_id'] = i.version_id.string

        f = p.File_Area_Observational
        result ['file_name'] = os.path.basename(f.File.file_name.string)
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

def extract_collection_id(lid):
    return lid.split(':')[4]

def index(list, indexfunc):
    d = {}
    for item in list:
        key = indexfunc(item)
        d.setdefault(key, []).append(item)
    return d


if __name__ == '__main__':
    sys.exit(main())    .exte