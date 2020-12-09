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
import argparse
import logging
import time
from types import SimpleNamespace


from product import Product
from collection import Collection
import iotools
import validation
import inventory
import preprocess
import paths



LABEL_FILENAME_TEMPLATE = 'collection_{collection_id}_{major}.{minor}.xml'
INSTRUMENTS = ['703','G96','I52','V06']
IGNORE_FILES = ['signature.md5', '.autoxfer']
IGNORE_DATES = ['pds4', 'other']
DELETION_BASE = '/sbn/to_delete/'
BATCH_SIZE=100

COLLECTION_FILES = {
    "data_derived" : "collection_data_derived.xml",
    "data_raw" : "collection_data_raw.xml",
    "data_reduced": "collection_data_reduced.xml",
    "data_partially_processed": "collection_data_partially_processed.xml",
    "data_calibrated": "collection_data_calibrated.xml",
    "document" : "collection_document.xml",
}

def main(argv=None):
    '''
    Extract command line arguments, ensure that the script is not already running,
    and process the current upload directory.
    '''
    parser = argparse.ArgumentParser(description='Validate a PDS4 collection inventory against the directory')
    parser.add_argument('--basedir', help='The base directory for the delivered data', required=True)
    parser.add_argument('--destdir', help='The destination directory for the processed data', required=True)
    parser.add_argument('--skip-preprocessing', action='store_true', dest='skip_preprocessing', help='If enabled, will not preprocess the data and label files')
    parser.add_argument('--skip-data-preprocessing', action='store_true', dest='skip_data_preprocessing', help='If enabled, will not preprocess the data files')
    parser.add_argument('--skip-label-preprocessing', action='store_true', dest='skip_label_preprocessing', help='If enabled, will not preprocess the label files')
    parser.add_argument('--skip-validation', action='store_true', dest='skip_validation', help='If enabled, will not validate the data')
    parser.add_argument('--permissive-validation', action='store_true', dest='permissive_validation', help='If enabled, will continue even if there are validation errors')
    parser.add_argument('--skip-data-validation', action='store_true', dest='skip_data_validation', help='If enabled, will not validate the data')
    parser.add_argument('--skip-move', action='store_true', dest='skip_move', help='If enabled, will not move the data')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s|%(levelname)s|%(message)s', 
        filename="process_uploads_%s.log" % time.time())

    preprocessing_opts = SimpleNamespace(
        skip_preprocessing=args.skip_preprocessing,
        skip_data_preprocessing=args.skip_data_preprocessing,
        skip_label_preprocessing=args.skip_label_preprocessing
    )

    validation_opts = SimpleNamespace(
        skip_validation=args.skip_validation,
        skip_data_validation=args.skip_data_validation,
        permissive_validation=args.permissive_validation
    )

    logging.info("Basedir: %s, Destdir: %s", args.basedir, args.destdir)
    lockfile_run(args.basedir, args.destdir, preprocessing_opts, validation_opts, args.skip_move)

    return 0

def lockfile_run(basedir, destdir, preprocessing_opts, validation_opts, skip_move):
    '''
    Run a function on this directory if one isn't already running. This is
    enforced with a lockfile.
    '''
    lockfile = os.path.join(basedir, ".lockfile")
    if not os.path.exists(lockfile):
        with open(lockfile, "w") as lock:
            lock.write(".")
        try:
            process_upload_dir(basedir, destdir, preprocessing_opts, validation_opts, skip_move)
        finally:
            os.remove(lockfile)


def process_upload_dir(basedir, destdir, preprocessing_opts, validation_opts, skip_move):
    '''
    process an upload directory, assuming it has been validated.
    '''
    logging.info("Discovering products at: %s", basedir)
    loc = paths.Paths(basedir, destdir)
    products = list(discover_products(loc))


    logging.info("%i products discovered", len(products))

    logging.debug(products)
    lidvids = (product.keywords['lidvid'] for product in products)
    collection_lids = index(lidvids, extract_collection_id)

    logging.debug(lidvids)
    logging.debug(collection_lids)

    # check whitelist here
    #if not all(product_whitelisted(x) for x in products):
    #    raise Exception('Some products used software not on the whitelist')


    for batch in chunk(products, BATCH_SIZE):
        all_validation_failures = []

        if not preprocessing_opts.skip_preprocessing:
            for product in batch:
                preprocess_product(product, loc, preprocessing_opts.skip_data_preprocessing, preprocessing_opts.skip_label_preprocessing)
        if not validation_opts.skip_validation:
            validation_failures,_,_ = validation.validate_products(batch, validation_opts.skip_data_validation)
            if validation_failures:
                all_validation_failures.extend(validation_failures)
    if all_validation_failures and not validation_opts.permissive_validation:
        raise Exception('There were validation errors')

    if not skip_move:
        for product in products:
            move_product(product, loc)

    for collection_id in collection_lids:
        collection_products = [x for x in products if x.keywords['collection_id'] == collection_id]
        if collection_products:
            process_data_collection(loc, collection_products, collection_id)

    #deletion_area_dest = os.path.join(DELETION_BASE, "placeholder")
    # delete files from temporary directory/move to deletion area
    #logging.info("moving to %s", deletion_area_dest)


def discover_products(loc):
    '''
    Find all of the product labels in the directory and convert them
    to product objects
    '''
    return itertools.chain.from_iterable(
        process_inst_directory(loc, instrument) for instrument in INSTRUMENTS)


def process_inst_directory(loc, instrument):
    '''
    Processes the given instrument directory

    Inside of an instrument directory, the labels are organized in subdirectories by year.

    basedir: the absolute path the to the top-level source files
    instrument: the mpc code for the instrument
    '''
    logging.info("Processing instrument directory: %s", instrument)

    instdir = loc.datadir(instrument)
    logging.info("processing %s...", instdir)
    years = (x.name for x in os.scandir(instdir) if x.is_dir())

    return itertools.chain.from_iterable(
        process_year_directory(loc, instrument, year) for year in years)


def process_year_directory(loc, instrument, year):
    '''
    Processes the given year directory.

    Inside of a year directory, the labels are organized in subdirectories by date.

    yeardir: the absolute path to the files for the given year
    instrument: the mpc code of the instrument
    year: the year being processed
    '''
    logging.info("processing year directory %s/%s", instrument, year)
    yeardir = loc.datadir(instrument, year)
    dates = [x.name for x in os.scandir(yeardir) if x.is_dir() and x.name not in IGNORE_DATES]
    logging.info("dates found: %s", dates)

    return itertools.chain.from_iterable(
        process_data(loc, instrument, year, date) for date in dates)

def process_data(loc, instrument, year, date):
    '''
    Processes the data in a given data directory and label directory pair.

    This checks for a semaphore file before actually doing the processing.

    datadir: the absolute path to the actual data files
    labeldir: the absolute path to the label files
    '''
    logging.info("processing data directory %s/%s/%s", instrument, year, date)

    datadir = loc.datadir(instrument, year, date)
    labeldir = loc.labeldir(instrument, year, date)
    if semaphore_exists(datadir) and semaphore_exists(labeldir):
        return process_labels(datadir, labeldir, instrument, year, date)
    
    logging.warning("no semaphore: %s and %s", labeldir, datadir)
    return []

def process_labels(datadir, labeldir, instrument, year, date):
    '''
    Processes the data in a given data directory and label directory pair.

    datadir: the absolute path to the actual data files
    labeldir: the absolute path to the label files
    '''
    logging.info("Processing searching for labels in %s/%s/%s", instrument, year, date)
    files = (x.name for x in os.scandir(labeldir) if is_label(x))
    products = [Product(datadir, os.path.join(labeldir, infile), instrument, year, date) for infile in files]
    logging.info("%s products in %s/%s/%s", len(products), instrument, year, date)
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

def preprocess_product(product, loc, skip_data_preprocessing, skip_label_preprocessing):
    logging.debug("Preprocessing files for: %s", product.labelfilename)
    logging.debug(product.keywords)

    file_names=product.keywords['file_names'] if 'file_names' in product.keywords else [product.keywords['file_name']]
    if not file_names:
        raise Exception("No filenames in label:", product.labelfilename)

    if not skip_data_preprocessing:
        for file_name in file_names:
            src_data = loc.datadir(product.inst, product.year, product.date, file_name)
            preprocess.preprocess_datafile(src_data)

    if not skip_label_preprocessing:
        src_label = loc.labeldir(product.inst, product.year, product.date, product.labelfilename)
        preprocess.preprocess_labelfile(src_label, file_names)



def move_product(product, loc):
    '''
    move a product to the archive directory. For the current workflow, this will be a
    temporary directory on the processing server that will then get synced over
    to the archive direcory.
    '''
    logging.info("Moving files for: %s", product.labelfilename)
    logging.debug(product.keywords)

    collection_id = product.keywords['collection_id']

    datadir = loc.datadir(product.inst, product.year, product.date)
    dest_directory = loc.destdir(collection_id, product.inst, product.year, product.date)
    os.makedirs(dest_directory, exist_ok=True)

    file_names=product.keywords['file_names'] if 'file_names' in product.keywords else [product.keywords['file_name']]
    if not file_names:
        raise Exception("No filenames in label:", product.labelfilename)

    src_label = product.labelpath
    dest_label = os.path.join(dest_directory, product.labelfilename)
    logging.info('Moved from %s to %s', src_label, dest_label)
    os.rename(src_label, dest_label)

    for file_name in file_names:
        src_data = os.path.join(datadir, file_name)
        dest_data = os.path.join(dest_directory, file_name)
        logging.info('Moved from %s to %s', src_data, dest_data)
        os.rename(src_data, dest_data)


def process_data_collection(loc, collection_products, collection_id):
    '''
    Create the collection inventory and label.
    '''
    logging.info("Processing collection: %s", collection_id)
    collection_path = loc.destdir(collection_id)
    os.makedirs(collection_path, exist_ok=True)

    collection_labels = get_collection_labels(collection_path, collection_id)
    logging.debug(collection_labels)

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
    logging.info("writing to: %s", collection_path)
    logging.debug(contents)
    iotools.write_file(collection_path, contents)


def semaphore_exists(dirname):
    '''
    Verifies that a semaphore file exists in the given directory.
    '''
    logging.info("checking for semaphore in %s", dirname)
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

def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i+size]


if __name__ == '__main__':
    sys.exit(main())
