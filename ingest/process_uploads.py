#! /usr/bin/env python3
"""
Python script to process submissions from Catalina Sky Survey and convert them
to PDS4 format.
"""

import sys

import os
import os.path
import itertools
import logging
import math
import json
import datetime
import shutil
import typing
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, select_autoescape

import preflight
from discovery import Discovery

from pds4types import ModificationDetail
from product import Product, ObsNight
from collection import Collection
import iotools
import validation
import inventory
import preprocess
import paths

import options


BUNDLE_ID = "gbo.ast.catalina.survey"
LABEL_FILENAME_TEMPLATE = 'collection_{collection_id}_v{major}.{minor}.xml'
IGNORE_FILES = ['signature.md5', '.autoxfer']
DELETION_BASE = '/sbn/to_delete/'
BATCH_SIZE = 100

COLLECTION_FILES = {
    "data_derived": "collection_data_derived.xml",
    "data_raw": "collection_data_raw.xml",
    "data_reduced": "collection_data_reduced.xml",
    "data_partially_processed": "collection_data_partially_processed.xml",
    "data_calibrated": "collection_data_calibrated.xml",
    "calibration": "collection_calibration.xml",
    "document": "collection_document.xml",
    "miscellaneous": "collection_miscellaneous.xml",
}

env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "templates")),
    autoescape=select_autoescape()
)


def main() -> int:
    """
    Extract command line arguments, ensure that the script is not already running,
    and process the current upload directory.
    """
    opts = options.get_args()

    if opts.console:
        logfilename = None
    else:
        logfilebase = f"process_uploads_{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')}.log"
        os.makedirs(os.path.join(opts.location_opts.basedir, "logs"), exist_ok=True)
        logfilename = os.path.join(opts.location_opts.basedir, "logs", logfilebase)
        
        print(logfilename)

    loglevel = logging.DEBUG if opts.verbose else logging.INFO

    logging.basicConfig(level=loglevel,
                        format='%(asctime)s|%(levelname)s|%(message)s',
                        filename=logfilename)

    logging.info(f"Basedir: {opts.location_opts.basedir}, Destdir: {opts.location_opts.destdir}")
    lockfile_run(opts)

    return 0


def lockfile_run(opts: options.Opts) -> None:
    """
    Run a function on this directory if one isn't already running. This is
    enforced with a lockfile.
    """
    lockfile = os.path.join(opts.location_opts.basedir, ".lockfile")
    if os.path.exists(lockfile):
        logging.info(f"Lockfile found at {lockfile}, skipping processing")
    else:
        with open(lockfile, "w") as lock:
            lock.write(".")
        try:
            process_upload_dir(opts)
        finally:
            os.remove(lockfile)


def process_upload_dir(opts: options.Opts) -> None:
    """
    process an upload directory, assuming it has been validated.
    """
    logging.info(f"Discovering products at: {opts.location_opts.basedir}")
    loc = paths.Paths(opts.location_opts, BUNDLE_ID)
    discovery = Discovery(loc, opts.filter_opts)
    directories = limit_directories(discovery, list(discovery.discover_product_dirs()), opts.filter_opts)
    logging.info(f"Discovery complete, consolidating: {opts.location_opts.basedir}")
    logging.info(f'Discovered directories: {directories}')
    products = list(
        itertools.chain.from_iterable(
            discovery.discover_date_products(night) for night in directories))

    logging.info(f"{len(products)} products discovered")

    process_product_list(loc, opts, products)


def process_product_list(loc: paths.Paths, opts: options.Opts, products: list[Product]):
    lidvids = (product.lidvid() for product in products)
    collection_lids = index(lidvids, extract_collection_id)
    logging.debug(lidvids)
    logging.debug(collection_lids)
    # check whitelist here
    logdir = os.path.join(opts.location_opts.destdir, "validation")
    os.makedirs(logdir, exist_ok=True)
    successes, failures = validate_products(products, loc, opts.preprocessing_opts, opts.validation_opts, logdir)
    # assume all products succeeded if we are skipping validation
    if opts.validation_opts.skip_validation:
        successful_files = set((x.night, x.labelfilename) for x in products)
    else:
        successful_files = set([validation.extract_label_info(x.labelpath) for x in successes])
    failed_files = set([validation.extract_label_info(x.labelpath) for x in failures])
    logging.info(failed_files)

    if opts.postprocessing_opts.skip_collection_update or opts.postprocessing_opts.validate_only:
        logging.info("Skipping collection update")
    else:
        update_collections(collection_lids, loc, opts, products, successful_files)

    if opts.postprocessing_opts.skip_move:
        logging.info("Skipping move")
    else:
        for product in products:
            labelinfo = (product.night, product.labelfilename)
            move_product(product, loc, opts.postprocessing_opts, labelinfo not in successful_files)

    if opts.postprocessing_opts.validate_only:
        logging.info("Regnerating semaphores at destination")
        for night in set(p.night for p in products):
            night_loc = loc.fornight(night)
            recreate_semaphore(night_loc.validation_data_dir())
            recreate_semaphore(night_loc.validation_label_dir())
    logging.info("done")


def update_collections(collection_lids: Iterable[str],
                       loc: paths.Paths,
                       opts: options.Opts,
                       products: Iterable[Product],
                       successful_files: Iterable[tuple[ObsNight, str]]):
    for collection_id in collection_lids:
        collection_products = [x for x in products
                               if x.collection_id() == collection_id
                               and (x.night, x.labelfilename) in successful_files]
        if collection_products:
            collection_path = update_data_collection(loc,
                                                     collection_products,
                                                     collection_id,
                                                     opts.postprocessing_opts.preserve_collection_version)
            collection_failures, _, collection_result = \
                validation.run_validator(collection_path, loc.schemadir, False)
            if len(collection_failures) > 0:
                logging.warning(f"There were collection failures: {collection_result}")
                raise Exception("Collection validation failed")


def recreate_semaphore(dirname: str, filename: str = '.autoxfer') -> None:
    logging.info(f'recreating semaphore {filename} at {dirname}')
    with open(os.path.join(dirname, filename), 'w'):
        pass


def limit_directories(discovery: Discovery,
                      directories: list[ObsNight],
                      filter_opts: options.FilterOpts) -> list[ObsNight]:
    dates = set([night.date for night in directories])
    if filter_opts.specific_date is not None:
        dates = [d for d in dates if d == filter_opts.specific_date]
    if filter_opts.ignore_past_days is not None:
        dates = [d for d in dates if d not in discovery.build_ignore_dates(filter_opts.ignore_past_days)]
    if filter_opts.max_nights is not None:
        candidates = sorted(dates, key=parse_dir_date, reverse=True)
        candidates_with_products = (d2 for d2 in candidates
                                    if any(discovery.date_has_semaphore(night)
                                           and discovery.date_has_products(night)
                                           for night in directories if night.date == d2))
        dates = [x for x in itertools.islice(candidates_with_products, filter_opts.max_nights)]
    logging.info(f'Processing dates: {dates}')
    return [night for night in directories if night.date in dates]


def index(items: Iterable[str], indexfunc: typing.Callable[[str], str]) -> dict:
    """
    Indexes a list of objects based on the output of a supplied function
    """
    dictionary = {}
    for item in items:
        key = indexfunc(item)
        dictionary.setdefault(key, []).append(item)
    return dictionary


def extract_collection_id(lid: str) -> str:
    """
    Extracts the collection id component from a LID
    """
    return lid.split(':')[4]


def validate_products(products: list[Product],
                      loc: paths.Paths,
                      preprocessing_opts: options.PreprocessingOpts,
                      validation_opts: options.ValidationOpts,
                      logdir: str) -> tuple[list[validation.ValidationResult], list[validation.ValidationResult]]:
    """
    Preprocess and validates the products. 
    The files will be preprocessed in the same manner as after validation. This prevents the original 
    files from being altered if there are validation errors.
    """
    all_validation_failures = []
    all_successes = []

    if preprocessing_opts.skip_preprocessing:
        logging.info("Skipping temp preprocessing")
    if validation_opts.skip_validation:
        logging.info("Skipping validation")

    batch_count = math.ceil(len(products)/BATCH_SIZE)

    for (batch_num, batch) in enumerate(chunk(products, BATCH_SIZE)):
        logging.info(f"Validating a batch of {len(batch)} ({batch_num + 1}/{batch_count})...")
        preflighted = list(preflight.preflight_products(batch))
        if not preprocessing_opts.skip_preprocessing:
            for product in preflighted:
                preprocess_product(product, loc,
                                   preprocessing_opts.skip_data_preprocessing,
                                   preprocessing_opts.skip_label_preprocessing)
        if not validation_opts.skip_validation:
            validation_failures, successes, unfiltered = \
                validation.validate_products(preflighted, loc.schemadir, validation_opts.skip_data_validation)
            log_validation_run(unfiltered, logdir)
            if validation_failures:
                for failure in validation_failures:
                    write_failure(preflighted, logdir, loc, failure)
                all_validation_failures.extend(validation_failures)
            all_successes.extend(successes)
    if all_validation_failures and not validation_opts.permissive_validation:
        raise Exception('There were validation errors')

    return all_successes, all_validation_failures


def log_validation_run(output: str, logdir: str) -> None:
    logdate = datetime.datetime.now().strftime("%Y%m%dT%H%M%S.%f")
    logfilename = f"{logdate}.json"
    logfilepath = os.path.join(logdir, logfilename)
    with open(logfilepath, "w") as logfile:
        logfile.write(output)


def write_failure(batch: Iterable[Product],
                  logdir: str,
                  loc: paths.Paths,
                  failure: validation.ValidationResult) -> None:
    """
    Writes information about a failure to the disk. If possible, it will write it next to the file that
    failed.
    """
    label_info = validation.extract_label_info(failure.labelpath)
    night, failfile = label_info
    src_products = [x for x in batch if (x.night, x.labelfilename) == label_info]

    faildir = loc.product_dest_dir(src_products[0], True) if src_products else logdir
    os.makedirs(faildir, exist_ok=True)

    faillogpath = os.path.join(faildir, f"{failfile}.log")
    with open(faillogpath, "w") as f:
        json.dump(failure.src, f, indent=2)


def chunk(items: list[Product], size: int) -> Iterable[list[Product]]:
    """
    Subdivides a list into chunks of the given size
    """
    for i in range(0, len(items), size):
        yield items[i:i+size]


def preprocess_product(product: Product,
                       loc: paths.Paths,
                       skip_data_preprocessing: bool,
                       skip_label_preprocessing: bool) -> None:
    logging.debug(f"Preprocessing files for: {product.labelfilename}", )

    file_names = product.filenames()
    if not file_names:
        raise Exception("No filenames in label:", product.labelfilename)

    night_loc = loc.fornight(product.night)

    if skip_data_preprocessing:
        logging.info("Skipping preprocessing")
    else:
        for file_name in file_names:
            src_data = os.path.join(night_loc.datadir(), file_name)
            preprocess.preprocess_datafile(src_data)

    if skip_label_preprocessing:
        logging.info("Skipping label preprocessing")
    else:
        src_label = os.path.join(night_loc.labeldir(), product.labelfilename)
        preprocess.preprocess_labelfile(src_label, file_names)


def move_product(product: Product,
                 loc: paths.Paths,
                 postprocessing_opts:
                 options.PostprocessingOpts,
                 failed: bool) -> None:
    if postprocessing_opts.validate_only:
        move_product_to_prevaldiated(product, loc, postprocessing_opts, failed)
    else:
        move_product_to_collections(product, loc, postprocessing_opts, failed)


def move_product_to_prevaldiated(product: Product,
                                 loc: paths.Paths,
                                 postprocessing_opts: options.PostprocessingOpts,
                                 failed: bool) -> None:
    """
    move a product to the pre-validated directory. Future runs of this script can now skip the validation.
    """
    logging.info(f"Moving files for: {product.labelfilename}")
    night_loc = loc.fornight(product.night)
    datadir = night_loc.datadir()
    label_dest_directory = night_loc.validation_label_dir(failed)
    data_dest_directory = night_loc.validation_data_dir(failed)
    os.makedirs(label_dest_directory, exist_ok=True)
    os.makedirs(data_dest_directory, exist_ok=True)

    do_move(product, postprocessing_opts, datadir, label_dest_directory, data_dest_directory)


def move_product_to_collections(product: Product,
                                loc: paths.Paths,
                                postprocessing_opts: options.PostprocessingOpts,
                                failed: bool) -> None:
    """
    move a product to the archive directory. For the current workflow, this will be a
    temporary directory on the processing server that will then get synced over
    to the archive direcory.
    """
    logging.info(f"Moving files for: {product.labelfilename}")

    datadir = loc.fornight(product.night).datadir()
    dest_directory = loc.product_dest_dir(product, failed)
    os.makedirs(dest_directory, exist_ok=True)

    do_move(product, postprocessing_opts, datadir, dest_directory, dest_directory)


def do_move(product: Product,
            postprocessing_opts: options.PostprocessingOpts,
            datadir: str,
            label_dest_directory: str,
            data_dest_directory: str) -> None:

    file_names = product.filenames()
    if not file_names:
        raise Exception("No filenames in label:", product.labelfilename)

    src_label = product.labelpath
    dest_label = os.path.join(label_dest_directory, product.labelfilename)
    transfer_file(src_label, dest_label, postprocessing_opts)

    for file_name in file_names:
        actual_file_name = get_actual_file_name(datadir, file_name)
        if actual_file_name:
            src_data = os.path.join(datadir, actual_file_name)
            dest_data = os.path.join(data_dest_directory, actual_file_name)
            transfer_file(src_data, dest_data, postprocessing_opts)


def transfer_file(src: str, dest: str, postprocessing_opts: options.PostprocessingOpts) -> None:
    if postprocessing_opts.dry_move:
        logging.debug(f'Simulating move from {src} to {dest}')
    else:   
        if postprocessing_opts.copy_files:
            logging.debug(f'Copying from {src} to {dest}, size: {os.path.getsize(src)}')
            shutil.copy(src, dest)
        else:
            logging.debug(f'Moving from {src} to {dest}, size: {os.path.getsize(src)}')
            os.rename(src, dest)        


def get_actual_file_name(data_dir: str, file_name: str) -> typing.Optional[str]:
    suffixes = ['', '.gz', '.fz']
    file_names = [file_name + suffix for suffix in suffixes
                  if os.path.exists(os.path.join(data_dir, file_name + suffix))]
    if file_names:
        return file_names[0]
    return None


def update_data_collection(loc: paths.Paths,
                           collection_products: list[Product],
                           collection_id: str,
                           preserve_collection_version: bool) -> str:
    """
    Create the collection inventory and label.
    """
    logging.info(f"Processing collection: {collection_id}")
    collection_path = loc.collection_dir(collection_id)
    os.makedirs(collection_path, exist_ok=True)

    collection_labels = get_collection_labels(collection_path)
    logging.debug(f"{len(collection_labels)} labels found")

    start_dates = [x.start_date() for x
                   in collection_products
                   if x.start_date() and is_pds_date(x.start_date())] + \
                  [x.start_date() for x
                   in collection_labels
                   if x.start_date() and is_pds_date(x.start_date())]

    stop_dates = [x.stop_date() for x
                  in collection_products
                  if x.stop_date() and is_pds_date(x.stop_date())] + \
                 [x.stop_date() for x
                  in collection_labels
                  if x.stop_date() and is_pds_date(x.stop_date())]

    start_date = min(start_dates) if start_dates else None
    stop_date = max(stop_dates) if stop_dates else None
    obs_dates = sorted(set(x.night.date for x in collection_products if x.night.date), key=parse_dir_date)
    
    old_lidvid = get_last_version_number(collection_id, collection_labels)
    new_lidvid, record_count = merge_inventories(
        collection_path, collection_id, collection_products, old_lidvid, preserve_collection_version)
    previous_collection = collection_with_version(collection_labels, old_lidvid["major"], old_lidvid["minor"])
    modification_history = [x for x
                            in previous_collection.modification_history().modification_details
                            if x.version_id == "1.0"] if previous_collection else None
    latest_modification = create_modification_detail(new_lidvid, f"routine delivery for: {','.join(obs_dates)}")

    template_filename = COLLECTION_FILES.get(collection_id, "other_collection_template.xml")
    return write_collection(template_filename,
                            new_lidvid,
                            collection_path,
                            start_date,
                            stop_date,
                            record_count,
                            modification_history,
                            latest_modification)


def is_pds_date(value: str) -> bool:
    return value and value.startswith('20') and value.endswith('Z')


def parse_dir_date(x: str) -> datetime.datetime:
    return datetime.datetime.strptime(x, "%y%b%d")


def get_collection_labels(collection_path: str) -> list[Collection]:
    """
    Gets the most recent known version number for a collection
    """
    collection_files = [x for x in os.scandir(collection_path) if is_collection_file(x)]
    return [Collection(collection_path, x.name) for x in collection_files]
    

def is_collection_file(candidate: os.DirEntry) -> bool:
    """
    Determine if the passed in file is a collection file.
    """
    return candidate.name.startswith('collection') and candidate.name.endswith('.xml')


def merge_inventories(collection_path: str,
                      collection_id: str,
                      collection_products: list[Product],
                      old_lidvid: dict,
                      preserve_collection_version: bool):
    """
    Produces a new collection inventory file, and returns the lidvid for the
    new collection
    """
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


def get_last_version_number(collection_id: str, collection_labels: list[Collection]) -> dict:
    """
    Gets the most recent known version number for a collection
    """
    if collection_labels:
        collection_versions = [
            (x.majorversion(), x.minorversion())
            for x in collection_labels]
        major, minor = max(collection_versions)
        logging.debug(f"{collection_id} previous collection version: {major}.{minor}")
        return make_collection_lidvid(collection_id, major, minor)
    return make_collection_lidvid(collection_id, 0, 0)


def make_collection_lidvid(collection_id: str, major: int, minor: int) -> dict:
    """
    Creates a collection lidvid from its component parts
    """
    return {
        'major': major,
        'minor': minor,
        'collection_id': collection_id
    }


def collection_with_version(collection_labels: list[Collection], major: str, minor: str) -> Collection:
    candidates = [x for x in collection_labels if x.majorversion() == major and x.minorversion() == minor]
    return candidates[0] if candidates else None


def create_modification_detail(new_lidvid: dict, description: str) -> dict:
    return {
        "modification_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "version_id": f'{new_lidvid["major"]}.{new_lidvid["minor"]}',
        "description": description
    }


def write_collection(template_filename: str,
                     collection_lidvid: dict,
                     collection_dir: str,
                     start_date: str,
                     stop_date: str,
                     record_count: int,
                     modification_history: list[ModificationDetail],
                     latest_modification: dict) -> str:
    """
    Writes the collection label to a file.
    """
    template = env.get_template(template_filename)
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
    logging.info(f"writing to: {collection_path}")
    logging.debug(contents)
    iotools.write_file(collection_path, contents)
    return collection_path


if __name__ == '__main__':
    sys.exit(main())
