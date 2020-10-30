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
import functools

from product import Product
from collection import Collection
import iotools
import validation
import inventory
import preprocess


LABEL_FILENAME_TEMPLATE = 'collection_{collection_id}_{major}.{minor}.xml'
INSTRUMENTS = ['703','G96','I52','V06']
IGNORE_FILES = ['signature.md5', '.autoxfer']
IGNORE_DATES = ['pds4']
DELIVERY_BASE = '/data/test'
ARCHIVE_BASE = '/data/test_ready/'
DELETION_BASE = '/sbn/to_delete/'

COLLECTION_FILES = {
    "data_derived" : "data_collection_template.xml"
}

def main(argv=None):
    '''
    Extract command line arguments, ensure that the script is not already running,
    and process the current upload directory.
    '''
    if argv is None:
        argv = sys.argv

    basedir = argv[1]

    lockfile_run(basedir, process_upload_dir, basedir)

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


def process_upload_dir(basedir):
    '''
    process an upload directory, assuming it has been validated.
    '''
    print ("Discovering products at: " + basedir)
    products = list(discover_products(basedir))


    print (len(products), " products discovered")

    #print(products)
    lidvids = (product.keywords['lidvid'] for product in products)
    collection_lids = index(lidvids, extract_collection_id)

    #print (lidvids)
    #print (collection_lids)

    # check whitelist here
    #if not all(product_whitelisted(x) for x in products):
    #    raise Exception('Some products used software not on the whitelist')

    for product in products:
        preprocess_product(product, basedir)


    validation_results = [validation.validate_product() for product in products]
    validation_failures = [failures for failures, successes in validation_results if failures]
    if validation_failures:
        raise Exception('There were validation errors')

    for product in products:
        move_product(product, basedir)

    for collection_id in collection_lids:
        collection_products = [x for x in products if x.keywords['collection_id'] == collection_id]
        if collection_products:
            process_data_collection(collection_products, collection_id)

    #deletion_area_dest = os.path.join(DELETION_BASE, "placeholder")
    # delete files from temporary directory/move to deletion area
    #print("moving to " + deletion_area_dest)


def discover_products(basedir):
    '''
    Find all of the product labels in the directory and convert them
    to product objects
    '''
    return itertools.chain.from_iterable(
        process_inst_directory(basedir, instrument) for instrument in INSTRUMENTS)


def process_inst_directory(basedir, instrument):
    '''
    Processes the given instrument directory

    Inside of an instrument directory, the labels are organized in subdirectories by year.
    '''
    print ("Processing instrument directory", instrument)

    instdir = os.path.join(basedir, instrument)
    print ("processing " + instdir + "...")
    yeardir = lambda year: os.path.join(instdir, year)
    years = (x.name for x in os.scandir(instdir) if x.is_dir())

    return itertools.chain.from_iterable(
        process_year_directory(yeardir(year), instrument, year) for year in years)


def process_year_directory(yeardir, instrument, year):
    '''
    Processes the given year directory.

    Inside of a year directory, the labels are organized in subdirectories by date.
    '''
    print ("processing year directory", instrument, year)
    dates = [x.name for x in os.scandir(yeardir) if x.is_dir() and x.name not in IGNORE_DATES]
    print(dates)
    datadir = lambda date: os.path.join(yeardir, date)
    labeldir = lambda date: os.path.join(yeardir, "pds4", date)

    return itertools.chain.from_iterable(
        process_data(datadir(date), labeldir(date), instrument, year, date) for date in dates)

def process_data(datadir, labeldir, instrument, year, date):
    '''
    Processes the data in a given data directory and label directory pair.

    This checks for a semaphore file before actually doing the processing.
    '''
    print ("processing data directory", instrument, year, date)
    if semaphore_exists(datadir) and semaphore_exists(labeldir):
        return process_labels(labeldir, instrument, year, date)
    print("no semaphore")
    return []
    #update_archive(archive_dir, changes)

def process_labels(labeldir, instrument, year, date):
    '''
    Processes the data in a given data directory and label directory pair.
    '''
    files = (x.name for x in os.scandir(labeldir) if is_label(x))
    products = [Product(os.path.join(labeldir, infile), instrument, year, date) for infile in files]
    print(len(products), " products in ", instrument, year, date)
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

def preprocess_product(product, basedir):
    print ("Preprocessing files for:", product.labelfilename)
    print(product.keywords)

    # INSTRUMENT/YEAR/DATE
    datadir = os.path.join(product.inst, product.year, product.date)

    # INSTRUMENT/YEAR/pds4/DATE
    labeldir = os.path.join(product.inst, product.year, "pds4", product.date)

    file_names=product.keywords['file_names'] if 'file_names' in product.keywords else [product.keywords['file_name']]
    if not file_names:
        raise Exception("No filenames in label:", product.labelfilename)

    src_label = os.path.join(basedir, labeldir, product.labelfilename)
    preprocess.preprocess_labelfile(src_label, file_names)

    for file_name in file_names:
        src_data = os.path.join(basedir, datadir, file_name)
        preprocess.preprocess_datafile(src_data)


def move_product(product, basedir):
    '''
    move a product to the archive directory. For the current workflow, this will be a
    temporary directory on the processing server that will then get synced over
    to the archive direcory.
    '''
    print ("Moving files for:", product.labelfilename)
    print(product.keywords)

    # INSTRUMENT/YEAR/DATE
    datadir = os.path.join(product.inst, product.year, product.date)

    # INSTRUMENT/YEAR/pds4/DATE
    labeldir = os.path.join(product.inst, product.year, "pds4", product.date)

    collection_id = product.keywords['collection_id']

    dest_directory = os.path.join(ARCHIVE_BASE, collection_id, datadir)
    os.makedirs(dest_directory, exist_ok=True)

    file_names=product.keywords['file_names'] if 'file_names' in product.keywords else [product.keywords['file_name']]
    if not file_names:
        raise Exception("No filenames in label:", product.labelfilename)

    src_label = os.path.join(basedir, labeldir, product.labelfilename)
    dest_label = os.path.join(dest_directory, product.labelfilename)
    print('Moved from %s to %s' % (src_label, dest_label))
    os.rename(src_label, dest_label)

    for file_name in file_names:
        src_data = os.path.join(basedir, datadir, file_name)
        dest_data = os.path.join(dest_directory, file_name)
        print('Moved from %s to %s' % (src_data, dest_data))
        os.rename(src_data, dest_data)


def process_data_collection(collection_products, collection_id):
    '''
    Create the collection inventory and label.
    '''
    print("Processing collection:", collection_id)
    collection_path = os.path.join(ARCHIVE_BASE, collection_id)
    os.makedirs(collection_path, exist_ok=True)

    collection_labels = get_collection_labels(collection_path, collection_id)
    print(collection_labels)

    start_dates = [x.keywords['start_date'] for x in collection_products if 'start_date' in x.keywords] + multilookup(collection_labels, 'start_date')
    stop_dates = [x.keywords['stop_date'] for x in collection_products if 'stop_date' in x.keywords] + multilookup(collection_labels, 'stop_date')
    start_date = min(start_dates) if start_dates else None
    stop_date = max(stop_dates) if stop_dates else None
    
    new_lidvid = merge_inventories(collection_path, collection_id, collection_products, collection_labels)

    template_filename = COLLECTION_FILES.get(collection_id, "other_collection_template.xml")
    write_collection(template_filename,
                     new_lidvid,
                     collection_path,
                     start_date,
                     stop_date)

def merge_inventories(collection_path, collection_id, collection_products, collection_labels):
    '''
    Produces a new collection inventory file, and returns the lidvid for the
    new collection
    '''
    product_lidvids = [x.keywords['lidvid'] for x in collection_products]

    old_lidvid = get_last_version_number(collection_id, collection_labels)
    old_inv = inventory.read_inventory(old_lidvid, collection_path)
    new_inv = inventory.from_lidvids('P', product_lidvids)

    new_lidvid = make_collection_lidvid(collection_id, old_lidvid['major'] + 1, 0)

    inventory.write_inventory(inventory.merge(old_inv, new_inv), new_lidvid, collection_path)

    return new_lidvid

def multilookup(labels, keyword):
    '''
    Gets a value from every collection label passed in
    '''
    return [x.keywords[keyword] for x in labels if keyword in x.keywords]

def get_last_version_number(collection_id, collection_labels):
    '''
    Gets the most recent known version number for a collection
    '''
    if collection_labels:
        collection_versions = [
            (x.keywords['major'], x.keywords['minor'])
            for x in collection_labels]
        major, minor = max(collection_versions)
        return make_collection_lidvid(collection_id, major, minor)
    return make_collection_lidvid(collection_id, 0, 0)

def get_collection_labels(collection_path, collection_id):
    '''
    Gets the most recent known version number for a collection
    '''
    collection_files = [x for x in os.scandir(collection_path) if is_collection_file(x)]
    return [Collection(collection_path, x.name) for x in collection_files]
    


def make_collection_lidvid(collection_id, major, minor):
    '''
    Creates a collection lidvid from its component parts
    '''
    return {
        'major': major,
        'minor': minor,
        'collection_id': collection_id
    }


def is_collection_file(candidate):
    '''
    Determine if the passed in file is a collection file.
    '''
    return candidate.name.startswith('collection') and candidate.name.endswith('.xml')




def write_collection(template_filename,
                     collection_lidvid,
                     collection_dir,
                     start_date,
                     stop_date):
    '''
    Writes the collection label to a file.
    '''
    template = iotools.read_file(template_filename)
    contents = template.format(
        collection_id=collection_lidvid['collection_id'],
        major=collection_lidvid['major'],
        minor=collection_lidvid['minor'],
        start_date=start_date,
        stop_date=stop_date,
        file_size=0,
        record_count=0)
    collection_filename = LABEL_FILENAME_TEMPLATE.format(**collection_lidvid)
    collection_path = os.path.join(collection_dir, collection_filename)
    print("writing to: ", collection_path)
    #print(contents)
    iotools.write_file(collection_path, contents)

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
    print ("checking for semaphore in", dirname)
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


if __name__ == '__main__':
    sys.exit(main())
