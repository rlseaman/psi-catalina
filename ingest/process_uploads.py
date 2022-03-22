#! /usr/bin/env python3
'''
Python script to process submissions from Catalina Sky Survey and convert them
to PDS4 format.
'''

from operator import mod
import sys

import os
import os.path
import itertools
import subprocess
import functools
import argparse
import logging
import time
import math
import json
from types import SimpleNamespace
import datetime
import shutil
from jinja2 import Environment, FileSystemLoader, select_autoescape
from product import Product
from collection import Collection
import iotools
import validation
import inventory
import preprocess
import paths



BUNDLE_ID = "gbo.ast.catalina.survey"
LABEL_FILENAME_TEMPLATE = 'collection_{collection_id}_v{major}.{minor}.xml'
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
    "calibration": "collection_calibration.xml",
    "document" : "collection_document.xml",
    "miscellaneous" : "collection_miscellaneous.xml",
}

env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "templates")),
    autoescape=select_autoescape()
)


def main(argv=None):
    '''
    Extract command line arguments, ensure that the script is not already running,
    and process the current upload directory.
    '''
    args = get_args()

    if args.console:
        logfilename = None
    else:
        logfilebase = "process_uploads_%s.log" % datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        os.makedirs(os.path.join(args.basedir, "logs"), exist_ok=True)
        logfilename=os.path.join(args.basedir, "logs", logfilebase)
        
        print(logfilename)

    loglevel = logging.DEBUG if args.verbose else logging.INFO

    logging.basicConfig(level=loglevel,
        format='%(asctime)s|%(levelname)s|%(message)s', 
        filename=logfilename)

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
    
    postprocessing_opts = SimpleNamespace(
        skip_move=args.skip_move,
        dry_move=args.dry_move,
        copy_files=args.copy_files,
        skip_collection_update=args.skip_collection_update,
        preserve_collection_version=args.preserve_collection_version
    )

    filter_opts = SimpleNamespace(
        specific_date = args.specific_date,
        specific_instrument = args.specific_instrument,
        max_products = args.max_products,
        max_nights = args.max_nights,
        ignore_past_days = args.ignore_past_days
    )

    logging.info("Basedir: %s, Destdir: %s", args.basedir, args.destdir)
    lockfile_run(args.basedir, args.destdir, args.schemadir, preprocessing_opts, validation_opts, postprocessing_opts, filter_opts)

    return 0

def get_args():
    parser = argparse.ArgumentParser(description='Validate a PDS4 collection inventory against the directory')
    parser.add_argument('--basedir', 
                        help='The base directory for the delivered data', 
                        required=True)
    parser.add_argument('--destdir', 
                        help='The destination directory for the processed data', 
                        required=True)
    parser.add_argument('--schemadir', 
                        help='The directory for the schema files', 
                        required=True)
    parser.add_argument('--specific-date', 
                        dest='specific_date', 
                        help='If provided, will only process the specified date')
    parser.add_argument('--specific-instrument', 
                        dest='specific_instrument', 
                        help='If provided, will only process the specified instrument')
    parser.add_argument('--skip-preprocessing', 
                        action='store_true', dest='skip_preprocessing', 
                        help='If enabled, will not preprocess the data and label files')
    parser.add_argument('--skip-data-preprocessing', 
                        action='store_true', dest='skip_data_preprocessing', 
                        help='If enabled, will not preprocess the data files')
    parser.add_argument('--skip-label-preprocessing', 
                        action='store_true', 
                        dest='skip_label_preprocessing', 
                        help='If enabled, will not preprocess the label files')
    parser.add_argument('--skip-validation', 
                        action='store_true', 
                        dest='skip_validation', 
                        help='If enabled, will not validate the data')
    parser.add_argument('--permissive-validation', 
                        action='store_true', dest='permissive_validation', 
                        help='If enabled, will continue even if there are validation errors')
    parser.add_argument('--skip-data-validation', 
                        action='store_true', 
                        dest='skip_data_validation', 
                        help='If enabled, will not validate the data')
    parser.add_argument('--skip-move', 
                        action='store_true', 
                        dest='skip_move', 
                        help='If enabled, will not move the data')
    parser.add_argument('--dry-move', 
                        action='store_true', 
                        dest='dry_move', 
                        help='If enabled, will not move the data, but will log the calculated destination')
    parser.add_argument('--copy-files', 
                        action='store_true', 
                        dest='copy_files', 
                        help='If enabled, will not move the data, but will copy it instead')
    parser.add_argument('--skip-collection-update', 
                        action='store_true', 
                        dest='skip_collection_update', 
                        help='If enabled, will not update the collection inventory or label')
    parser.add_argument('--preserve-collection-version', 
                        action='store_true', 
                        dest='preserve_collection_version', 
                        help='If enabled, will not update the collection version numbers')
    parser.add_argument('--console', 
                        action='store_true', 
                        dest='console', 
                        help='If enabled, will log to console instead of log file')
    parser.add_argument('--verbose', 
                        action='store_true', 
                        dest='verbose', 
                        help='If enabled, will add more info to logs')
    parser.add_argument('--max-products', 
                        type=int,
                        dest='max_products', 
                        help='The maximum number of products to process in a single run')
    parser.add_argument('--max-nights', 
                        type=int,
                        dest='max_nights', 
                        help='The maximum number of nights to process in a single run')
    parser.add_argument('--ignore-past-days', 
                        type=int,
                        default=0,
                        dest='ignore_past_days', 
                        help='Ignores products dated in the past x number of days. This will give products time to accumulate before processing')

    return parser.parse_args()


def lockfile_run(basedir, destdir, schemadir, preprocessing_opts, validation_opts, postprocesing_opts, filter_opts):
    '''
    Run a function on this directory if one isn't already running. This is
    enforced with a lockfile.
    '''
    lockfile = os.path.join(basedir, ".lockfile")
    if os.path.exists(lockfile):
        logging.info("Lockfile found at %s, skipping processing", lockfile)
    else:
        with open(lockfile, "w") as lock:
            lock.write(".")
        try:
            process_upload_dir(basedir, destdir, schemadir, preprocessing_opts, validation_opts, postprocesing_opts, filter_opts)
        finally:
            os.remove(lockfile)


def process_upload_dir(basedir, destdir, schemadir, preprocessing_opts, validation_opts, postprocesing_opts, filter_opts):
    '''
    process an upload directory, assuming it has been validated.
    '''
    logging.info("Discovering products at: %s", basedir)
    loc = paths.Paths(basedir, destdir, BUNDLE_ID, schemadir)
    directories = limit_directories(list(discover_product_dirs(loc, filter_opts)), filter_opts)
    logging.info("Discovey complete, consolidating: %s", basedir)
    logging.info(f'Discovered directories: {directories}')
    products = list(itertools.chain.from_iterable(discover_date_products(loc, inst, year, d) for inst, year, d in directories))


    logging.info("%i products discovered", len(products))

    #logging.debug(products)
    lidvids = (product.lidvid() for product in products)
    collection_lids = index(lidvids, extract_collection_id)

    logging.debug(lidvids)
    logging.debug(collection_lids)

    # check whitelist here
    #if not all(product_whitelisted(x) for x in products):
    #    raise Exception('Some products used software not on the whitelist')

    logdir = os.path.join(destdir,"validation")
    os.makedirs(logdir, exist_ok=True)

    failures = validate_products(products, loc, preprocessing_opts, validation_opts, logdir)
    failed_files = set([validation.extract_label_info(x['label']) for x in failures])
    logging.info(failed_files)

    if postprocesing_opts.skip_move:
        logging.info("Skipping move")
    else:
        for product in products:
            move_product(product, loc, postprocesing_opts, (product.inst, product.year, product.date, product.labelfilename) in failed_files)

    if postprocesing_opts.skip_collection_update:
        logging.info("Skipping collection update")
    else:
        for collection_id in collection_lids:
            collection_products = [x for x in products if x.collection_id() == collection_id and x.labelfilename not in failed_files]
            if collection_products:
                update_data_collection(loc, collection_products, collection_id, postprocesing_opts.preserve_collection_version)

    #deletion_area_dest = os.path.join(DELETION_BASE, "placeholder")
    # delete files from temporary directory/move to deletion area
    #logging.info("moving to %s", deletion_area_dest)
    logging.info("done")

def limit_directories(directories, filter_opts):
    dates = set([d for inst, year, d in directories])
    if filter_opts.specific_date is not None:
        dates = [d for d in dates if d == filter_opts.specific_date]
    if filter_opts.ignore_past_days is not None:
        dates = [d for d in dates if d not in build_ignore_dates(filter_opts.ignore_past_days)]
    if filter_opts.max_nights is not None:
        dates = sorted(dates, key=parseDirDate, reverse=True)[:filter_opts.max_nights]
    logging.info(f'Processing dates: {dates}')
    return [(inst, year, d) for inst,year,d in directories if d in dates]


def discover_product_dirs(loc, filter_opts):
    '''
    Find all of the product labels in the directory and convert them
    to product objects
    '''
    instruments = [filter_opts.specific_instrument] if filter_opts.specific_instrument else INSTRUMENTS
    return itertools.chain.from_iterable(
        process_inst_directory(loc, instrument, filter_opts) for instrument in instruments)


def process_inst_directory(loc, instrument, filter_opts):
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
        process_year_directory(loc, instrument, year, filter_opts) for year in years)


def process_year_directory(loc, instrument, year, filter_opts):
    '''
    Processes the given year directory.

    Inside of a year directory, the labels are organized in subdirectories by date.

    yeardir: the absolute path to the files for the given year
    instrument: the mpc code of the instrument
    year: the year being processed
    '''
    logging.info("processing year directory %s/%s", instrument, year)
    yeardir = loc.datadir(instrument, year)
    days_to_ignore = IGNORE_DATES + build_ignore_dates(filter_opts.ignore_past_days)
    discovered_dates = [x.name for x in os.scandir(yeardir) if x.is_dir() and os.access(x, os.W_OK) and x.name not in days_to_ignore]
    return [(instrument, year, d) for d in discovered_dates if date_has_semaphore(loc, instrument, year, d) and date_has_products(loc, instrument, year, d)]


def build_ignore_dates(num_days):
    '''
    Builds a list of days to ignore when processing. This will be the past n days
    '''
    deltas = [datetime.timedelta(days=x) for x in range (0, num_days)]
    dates=[datetime.datetime.now() - delta for delta in deltas]
    datestrs = [dt.strftime("%y%b%d") for dt in dates]
    return datestrs

def date_has_semaphore(loc, instrument, year, date):
    datadir = loc.datadir(instrument, year, date)
    labeldir = loc.labeldir(instrument, year, date)
    return semaphore_exists(datadir) and semaphore_exists(labeldir)

def date_has_products(loc, instrument, year, date):
    labeldir = loc.labeldir(instrument, year, date)
    return len(get_labels(labeldir))

def discover_date_products(loc, instrument, year, date):
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
        return labels_to_products(datadir, labeldir, instrument, year, date)
    
    logging.warning("no semaphore: %s and %s", labeldir, datadir)
    return []


def semaphore_exists(dirname):
    '''
    Verifies that a semaphore file exists in the given directory.

    dirname: the absolute path of the directory to check
    '''
    logging.info("checking for semaphore in %s", dirname)
    semaphore_file = os.path.join(dirname, '.autoxfer')
    return os.path.exists(semaphore_file)


def labels_to_products(datadir, labeldir, instrument, year, date):
    '''
    Processes the data in a given data directory and label directory pair.

    datadir: the absolute path to the actual data files
    labeldir: the absolute path to the label files
    '''
    logging.info("Processing searching for labels in %s/%s/%s", instrument, year, date)
    files = get_labels(labeldir)
    empty_labels = [x for x in files if os.path.getsize(os.path.join(labeldir, x)) == 0]
    if empty_labels:
        logging.warn("Empty labels in %s: %s", labeldir, empty_labels)

    unwritable_labels = [x for x in files if not os.access(os.path.join(labeldir, x), os.W_OK)]
    if unwritable_labels:
        logging.warn("Unwritable labels in %s: %s", labeldir, unwritable_labels)

    usable_labels = [x for x in files if x not in empty_labels and x not in unwritable_labels]
    
    products = (Product(datadir, os.path.join(labeldir, infile), instrument, year, date) for infile in usable_labels)
    #logging.info("%s products in %s/%s/%s", len(products), instrument, year, date)
    logging.info("discovery complete in %s/%s/%s", instrument, year, date)
    return products

def get_labels(labeldir):
    return [x.name for x in os.scandir(labeldir) if is_label(x)]

def product_whitelisted(product):
    '''
    determines if all of the software for the product has been approved
    '''
    if product.software:
        return all([software_whitelisted(x) for x in product.software()])
    return True


def software_whitelisted(software):
    '''
    determines if a single piece of software has been approved
    '''
    return True


def index(items, indexfunc):
    '''
    Indexes a list of objects based on the output of a supplied function
    '''
    dictionary = {}
    for item in items:
        key = indexfunc(item)
        dictionary.setdefault(key, []).append(item)
    return dictionary


def extract_collection_id(lid):
    '''
    Extracts the collection id component from a LID
    '''
    return lid.split(':')[4]


def validate_products(products, loc, preprocessing_opts, validation_opts, logdir):
    '''
    Preprocess and validates the products. 
    The files will be preprocessed in the same manner as after validation. This prevents the original 
    files from being altered if there are validation errors.
    '''
    all_validation_failures = []

    if preprocessing_opts.skip_preprocessing:
        logging.info("Skipping temp preprocessing")
    if validation_opts.skip_validation:
        logging.info("Skipping validation")

    batch_count = math.ceil(len(products)/BATCH_SIZE)

    for (batch_num, batch) in enumerate(chunk(products, BATCH_SIZE)):
        logging.info("Validating a batch of %s (%s/%s)...", len(batch), batch_num + 1, batch_count)
        if not preprocessing_opts.skip_preprocessing:
            for product in batch:
                preprocess_product(product, loc, preprocessing_opts.skip_data_preprocessing, preprocessing_opts.skip_label_preprocessing)
        if not validation_opts.skip_validation:
            validation_failures,_,unfiltered = validation.validate_products(batch, loc.schemadir, validation_opts.skip_data_validation)
            log_validation_run(unfiltered, logdir)
            if validation_failures:
                for failure in validation_failures:
                    writeFailure(batch, logdir, loc, failure)
                all_validation_failures.extend(validation_failures)
    if all_validation_failures and not validation_opts.permissive_validation:
        raise Exception('There were validation errors')

    return all_validation_failures

def log_validation_run(output, logdir):
    logdate = datetime.datetime.now().strftime("%Y%m%dT%H%M%S.%f")
    logfilename = logdate + ".json"
    logfilepath = os.path.join(logdir, logfilename)
    with open(logfilepath, "w") as logfile:
        logfile.write(output)

'''
Writes information about a failure to the disk. If possible, it will write it next to the file that
failed.
'''
def writeFailure(batch, logdir, loc, failure):
    label_info = validation.extract_label_info(failure['label'])
    inst, year, dateval, failfile = label_info
    src_products = [x for x in batch if (x.inst, x.year, x.date, x.labelfilename) == label_info]

    faildir = loc.productDestDir(src_products[0], True) if src_products else logdir
    os.makedirs(faildir, exist_ok=True)

    faillogpath = os.path.join(faildir, failfile + ".log")
    with open(faillogpath, "w") as f:
        json.dump(failure, f, indent=2)



def chunk(items, size):
    '''
    Subdivides a list into chunks of the given size
    '''
    for i in range(0, len(items), size):
        yield items[i:i+size]


def preprocess_product(product, loc, skip_data_preprocessing, skip_label_preprocessing):
    logging.debug("Preprocessing files for: %s", product.labelfilename)

    file_names=product.filenames()
    if not file_names:
        raise Exception("No filenames in label:", product.labelfilename)

    if skip_data_preprocessing:
        logging.info("Skipping preprocessing")
    else:
        for file_name in file_names:
            src_data = loc.datadir(product.inst, product.year, product.date, file_name)
            preprocess.preprocess_datafile(src_data)

    if skip_label_preprocessing:
        logging.info("Skipping label preprocessing")
    else:
        src_label = loc.labeldir(product.inst, product.year, product.date, product.labelfilename)
        preprocess.preprocess_labelfile(src_label, file_names)



def move_product(product, loc, postprocessing_opts, failed):
    '''
    move a product to the archive directory. For the current workflow, this will be a
    temporary directory on the processing server that will then get synced over
    to the archive direcory.
    '''
    logging.info("Moving files for: %s", product.labelfilename)

    datadir = loc.datadir(product.inst, product.year, product.date)
    dest_directory = loc.productDestDir(product, failed)
    os.makedirs(dest_directory, exist_ok=True)

    file_names=product.filenames()
    if not file_names:
        raise Exception("No filenames in label:", product.labelfilename)

    src_label = product.labelpath
    dest_label = os.path.join(dest_directory, product.labelfilename)
    transfer_file(src_label, dest_label, postprocessing_opts)

    for file_name in file_names:
        actual_file_name = get_actual_file_name(datadir, file_name)
        if actual_file_name:
            src_data = os.path.join(datadir, actual_file_name)
            dest_data = os.path.join(dest_directory, actual_file_name)
            transfer_file(src_data, dest_data, postprocessing_opts)


def transfer_file(src, dest, postprocessing_opts):
    if postprocessing_opts.dry_move:
        logging.debug('Simulating move from %s to %s', src, dest)
    else:   
        if postprocessing_opts.copy_files:
            logging.debug('Copying from %s to %s', src, dest)
            shutil.copy(src, dest)
        else:
            logging.debug('Moving from %s to %s', src, dest)
            os.rename(src, dest)        


def get_actual_file_name(data_dir, file_name):
    suffixes = ['', '.gz', '.fz']
    file_names = [file_name + suffix for suffix in suffixes if os.path.exists(os.path.join(data_dir, file_name + suffix))]
    if file_names:
        return file_names[0]
    return None
    #raise(Exception('cannot find file:' + os.path.join(data_dir, file_name)))



def update_data_collection(loc, collection_products: list, collection_id, preserve_collection_version):
    '''
    Create the collection inventory and label.
    '''
    logging.info("Processing collection: %s", collection_id)
    collection_path = loc.destdir(collection_id)
    os.makedirs(collection_path, exist_ok=True)

    collection_labels = get_collection_labels(collection_path, collection_id)
    logging.debug("%s labels found", len(collection_labels))

    start_dates = [x.start_date() for x in collection_products + collection_labels if x.start_date()]
    stop_dates = [x.stop_date() for x in collection_products + collection_labels if x.stop_date()]
    start_date = min(start_dates) if start_dates else None
    stop_date = max(stop_dates) if stop_dates else None
    obs_dates = sorted(set([x.date for x in collection_products if x.date]), key=parseDirDate)
    
    old_lidvid = get_last_version_number(collection_id, collection_labels)
    new_lidvid, record_count = merge_inventories(collection_path, collection_id, collection_products, old_lidvid, preserve_collection_version)
    previous_collection = collection_with_version(collection_labels, old_lidvid["major"], old_lidvid["minor"])
    modification_history = [x for x in previous_collection.modification_history() if x["version_id"] == "1.0"] if previous_collection else []
    latest_modification=create_modification_detail(new_lidvid, "routine delivery for: " + ",".join(obs_dates))


    template_filename = COLLECTION_FILES.get(collection_id, "other_collection_template.xml")
    write_collection(template_filename,
                     new_lidvid,
                     collection_path,
                     start_date,
                     stop_date,
                     record_count,
                     modification_history,
                     latest_modification)

def parseDirDate(x):
    return datetime.datetime.strptime(x, "%y%b%d")

def get_collection_labels(collection_path, collection_id):
    '''
    Gets the most recent known version number for a collection
    '''
    collection_files = [x for x in os.scandir(collection_path) if is_collection_file(x)]
    return [Collection(collection_path, x.name) for x in collection_files]
    

def is_collection_file(candidate):
    '''
    Determine if the passed in file is a collection file.
    '''
    return candidate.name.startswith('collection') and candidate.name.endswith('.xml')


def merge_inventories(collection_path, collection_id, collection_products, old_lidvid, preserve_collection_version):
    '''
    Produces a new collection inventory file, and returns the lidvid for the
    new collection
    '''
    product_lidvids = [x.lidvid() for x in collection_products]

    old_inv = inventory.read_inventory(old_lidvid, collection_path)
    new_inv = inventory.from_lidvids('P', product_lidvids)

    
    if preserve_collection_version:
        new_major = max(old_lidvid['major'], 1)
        new_minor = old_lidvid['minor']
    else:
        new_major = old_lidvid['major'] + 1
        new_minor = 0


    new_lidvid = make_collection_lidvid(collection_id, new_major, new_minor)
    merged_inv = inventory.merge(old_inv, new_inv)

    inventory.write_inventory(merged_inv, new_lidvid, collection_path)

    return new_lidvid, len(merged_inv)


def get_last_version_number(collection_id, collection_labels):
    '''
    Gets the most recent known version number for a collection
    '''
    if collection_labels:
        collection_versions = [
            (x.majorversion(), x.minorversion())
            for x in collection_labels]
        major, minor = max(collection_versions)
        logging.debug("%s previous collection version: %s.%s", collection_id, major, minor)
        return make_collection_lidvid(collection_id, major, minor)
    return make_collection_lidvid(collection_id, 0, 0)



def make_collection_lidvid(collection_id, major, minor):
    '''
    Creates a collection lidvid from its component parts
    '''
    return {
        'major': major,
        'minor': minor,
        'collection_id': collection_id
    }

def collection_with_version(collection_labels:list, major:str, minor:str):
    candidates = [x for x in collection_labels if x.majorversion() == major and x.minorversion() == minor]
    return candidates[0] if candidates else None

def create_modification_detail(new_lidvid, description):
    return {
        "modification_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "version_id": f'{new_lidvid["major"]}.{new_lidvid["minor"]}',
        "description": description
    }


def write_collection(template_filename,
                     collection_lidvid,
                     collection_dir,
                     start_date,
                     stop_date,
                     record_count,
                     modification_history,
                     latest_modification):
    '''
    Writes the collection label to a file.
    '''
    template=env.get_template(template_filename)
    contents = template.render(
        collection_id=collection_lidvid['collection_id'],
        major=collection_lidvid['major'],
        minor=collection_lidvid['minor'],
        start_date=start_date,
        stop_date=stop_date,
        file_size=0,
        record_count=record_count,
        year=datetime.datetime.now().strftime("%Y"),
        modification_history=modification_history,
        latest_modification=latest_modification)
    collection_filename = LABEL_FILENAME_TEMPLATE.format(**collection_lidvid)
    collection_path = os.path.join(collection_dir, collection_filename)
    logging.info("writing to: %s", collection_path)
    logging.debug(contents)
    iotools.write_file(collection_path, contents)



def is_label(candidate):
    '''
    Determines if the given file is a label file.
    '''
    return candidate.name.endswith('.xml') and check_writable(candidate)

def check_writable(candidate):
    if os.access(candidate, os.W_OK):
        return True
    logging.warning("Label %s is not writable. Skipping...", candidate.name)
    return False


if __name__ == '__main__':
    sys.exit(main())
