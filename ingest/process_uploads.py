#! /usr/bin/env python3
'''
Python script to process submissions from Catalina Sky Survey and convert them
to PDS4 format.
'''

import sys

import os
import os.path
import itertools
import subprocess
from product import Product
from collection import Collection
import validation


INSTRUMENTS = ['G96']
IGNORE_FILES = ['signature.md5', '.autoxfer']
IGNORE_DATES = ['pds4']
DEST_BASE = '.'

def main(argv=None):
    '''
    Extract command line arguments, ensure that the script is not already running,
    and process the current upload directory.
    '''
    if argv is None:
        argv = sys.argv

    basedir = argv[1]

    lockfile_run(basedir, validate_run, basedir, process_upload_dir, basedir)

    return 0

def lockfile_run(basedir, func, *args):
    '''
    Run a function on this directory if one isn't already running. This is
    enforced with a lockfile.
    '''
    lockfile = os.path.join(basedir, ".lockfile")
    if not os.path.exists(lockfile):
        with open(lockfile, "w") as lock:
            lock.write(".")
        try:
            func(*args)
        finally:
            os.remove(lockfile)

def validate_run(basedir, func, *args):
    '''
    Run a function on this directory if the files in it are valid.
    '''
    validation_result = validation.Validation(basedir)
    if not validation_result.failures:
        func(*args)
    else:
        raise Exception('There were validation errors')

def process_upload_dir(basedir):
    '''
    process an upload directory, assuming it has been validated.
    '''
    products = list(discover_products(basedir))
    lidvids = (product.keywords['lidvid'] for product in products)
    collection_lids = index(lidvids, extract_collection_id)

    # check whitelist here
    for product in products:
        if not product_whitelisted(product):
            raise Exception('Some products used software not on the whitelist')

    for product in products:
        move_product(product, basedir)

    for collection_id in collection_lids:
        collection_products = [x for x in products if x.keywords['collection_id'] == collection_id]
        if collection_products:
            process_collection(collection_products, collection_id)

    # move files to the archive here
    #subprocess.run(['rsync', './', 'sbnarchive:/dsk1/archive/pds4/non-mission/css'], cwd=DEST_BASE)


def discover_products(basedir):
    '''
    Find all of the product labels in the directory and convert them
    to product objects
    '''
    return itertools.chain.from_iterable(process_inst_directory(basedir, instrument)
                                         for instrument in INSTRUMENTS)


def process_inst_directory(basedir, instrument):
    '''
    Processes the given instrument directory

    Inside of an instrument directory, the labels are organized in subdirectories by year.
    '''
    instdir = os.path.join(basedir, instrument)
    yeardir = lambda year: os.path.join(instdir, year)
    years = (x.name for x in os.scandir(instdir) if x.is_dir())

    return itertools.chain.from_iterable(process_year_directory(yeardir(year), instrument, year)
                                         for year in years)


def process_year_directory(yeardir, instrument, year):
    '''
    Processes the given year directory.

    Inside of a year directory, the labels are organized in subdirectories by date.
    '''
    dates = (x.name for x in os.scandir(yeardir) if x.is_dir() and x.name not in IGNORE_DATES)
    datadir = lambda date: os.path.join(yeardir, date)
    labeldir = lambda date: os.path.join(yeardir, "pds4", date)

    return itertools.chain.from_iterable(
        process_data(datadir(date), labeldir(date), instrument, year, date)
        for date in dates)

def process_data(datadir, labeldir, instrument, year, date):
    '''
    Processes the data in a given data directory and label directory pair.

    This checks for a semaphore file before actually doing the processing.
    '''
    if semaphore_exists(datadir) and semaphore_exists(labeldir):
        return process_labels(labeldir, instrument, year, date)
    return []
    #update_archive(archive_dir, changes)

def process_labels(labeldir, instrument, year, date):
    '''
    Processes the data in a given data directory and label directory pair.
    '''
    files = (x.name for x in os.scandir(labeldir) if is_label(x))
    products = [Product(labeldir, infile, instrument, year, date) for infile in files]
    return products

def product_whitelisted(product):
    '''
    determines if all of the software for the product has been approved
    '''
    if 'software' in product.keywords:
        return all([software_whitelisted(x) for x in product.keywords['software']])
    return True

def software_whitelisted(software):
    '''
    determines if a single piece of software has been approved
    '''
    return True

def move_product(product, basedir):
    '''
    move a product to the archive directory
    '''
    datadir = os.path.join(product.inst, product.year, product.date)
    labeldir = os.path.join(product.inst, product.year, "pds4", product.date)

    collection_id = product.keywords['collection_id']
    product_directory = os.path.join(product.inst, product.year, product.date)
    dest_directory = os.path.join(DEST_BASE, collection_id, product_directory)
    os.makedirs(dest_directory, exist_ok=True)

    src_data = os.path.join(basedir, datadir, product.keywords['file_name'])
    dest_data = os.path.join(dest_directory, datadir, product.keywords['file_name'])
    print('Moved from %s to %s' % (src_data, dest_data))
    #os.rename(src_data, dest_data)

    src_label = os.path.join(basedir, labeldir, product.labelfilename)
    dest_label = os.path.join(dest_directory, datadir, product.labelfilename)
    print('Moved from %s to %s' % (src_label, dest_label))
    #os.rename(src_label, dest_label)


def process_collection(collection_products, collection_id):
    '''
    Create the collection inventory and label.
    '''
    collection_lidvids = [x.keywords['lidvid'] for x in collection_products]
    start_date = min([x.keywords['start_date'] for x in collection_products])
    stop_date = max([x.keywords['stop_date'] for x in collection_products])
    collection_path = os.path.join(DEST_BASE, collection_id)
    os.makedirs(collection_path, exist_ok=True)
    major, minor = get_last_version_number(collection_path)
    inventory = read_inventory(major, minor, collection_id, collection_path)
    inventory.extend(['P,' + x for x in collection_lidvids])
    newmajor = major + 1
    newminor = 0
    write_inventory(newmajor, newminor, inventory, collection_id, collection_path)

    template_filename = "collection_template.xml"
    write_collection(newmajor,
                     newminor,
                     template_filename,
                     collection_id,
                     collection_path,
                     start_date,
                     stop_date)

def get_last_version_number(collection_path):
    '''
    Gets the most recent known version number for a collection
    '''
    collection_files = [x for x in os.scandir(collection_path) if is_collection_file(x)]
    if collection_files:
        collection_labels = [Collection(collection_path, x.name) for x in collection_files]
        collection_versions = [
            (x.keywords['major'], x.keywords['minor'])
            for x in collection_labels]
        return max(collection_versions)
    return (0, 0)

def is_collection_file(candidate):
    '''
    Determine if the passed in file is a collection file.
    '''
    return candidate.name.startswith('collection') and candidate.name.endswith('.xml')

def read_inventory(major, minor, collection_id, collection_dir):
    '''
    Reads in the inventory for the most recent collection update before this one
    '''
    if major:
        collection_filename = 'collection_%s_%s.%s.csv' % (collection_id, major, minor)
        collection_path = os.path.join(collection_dir, collection_filename)
        return open(collection_path).readlines()
    return []

def write_inventory(major, minor, inventory, collection_id, collection_dir):
    '''
    Writes the collection inventory to a file
    '''
    collection_filename = 'collection_%s_%s.%s.csv' % (collection_id, major, minor)
    collection_path = os.path.join(collection_dir, collection_filename)
    write_file(collection_path, '\r\n'.join(inventory) + '\r\n')

def write_collection(major,
                     minor,
                     template_filename,
                     collection_id,
                     collection_dir,
                     start_date,
                     stop_date):
    '''
    Writes the collection label to a file.
    '''
    template = read_file(template_filename)
    contents = template.format(**{
        'collection_id': collection_id,
        'major': major,
        'minor': minor,
        'start_date': start_date,
        'stop_date': stop_date,
        'file_size': 0,
        'record_count': 0})
    collection_filename = 'collection_%s_%s.%s.xml' % (collection_id, major, minor)
    collection_path = os.path.join(collection_dir, collection_filename)
    write_file(collection_path, contents)

def update_archive(archive_dir, changes):
    '''
    Placeholder for code to actually upload data to the archive site
    '''
    print('updating %s' % archive_dir)
    for change in changes:
        print(change)

def semaphore_exists(dirname):
    '''
    Verifies that a semaphore file exists in the given directory.
    '''
    semaphore_file = os.path.join(dirname, '.autoxfer')
    return os.path.exists(semaphore_file)

def is_label(candidate):
    '''
    Determines if the given file is a label file.
    '''
    return candidate.name.endswith('.xml')

def find_files(dirname):
    '''
    Gets all of the files in a directory.
    '''
    filelists = [[os.path.join(subdir, f) for f in files] for subdir, _, files in os.walk(dirname)]
    return itertools.chain.from_iterable(filelists)

def extract_version(label):
    '''
    Extracts the version number from a collection label.
    '''
    product_element = label.Product_Collection
    if product_element:
        identification_area = product_element.Identification_Area
        version = identification_area.version_id.string
        return [int(x) for x in version.split(".")]

    return (0, 0)

def ignore(file):
    '''
    Determines if a file should be ignored when processing.
    '''
    return any((file.endswith(name) for name in IGNORE_FILES))

def extract_collection_id(lid):
    '''
    Extracts the collection id component from a LID
    '''
    return lid.split(':')[4]

def index(items, indexfunc):
    '''
    Indexes a list of objects based on the output of a supplied function
    '''
    dictionary = {}
    for item in items:
        key = indexfunc(item)
        dictionary.setdefault(key, []).append(item)
    return dictionary

def read_file(filename):
    '''
    One-liner to read a file
    '''
    with open(filename) as infile:
        return infile.read()

def write_file(filename, contents):
    '''
    One-liner to write a file
    '''
    path = os.path.dirname(filename)
    os.makedirs(path, exist_ok=True)
    with open(filename, "w") as outfile:
        outfile.write(contents)

if __name__ == '__main__':
    sys.exit(main())
