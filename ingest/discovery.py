import datetime
import itertools
import logging
import os
from dataclasses import dataclass
from typing import Iterable

import options
import paths
from product import Product


IGNORE_DATES = ['pds4', 'other']
INSTRUMENTS = ['703', 'G96', 'I52', 'V06']

@dataclass
class ObsNight:
    inst: str
    year: str
    date: str


def discover_product_dirs(loc: paths.Paths, filter_opts: options.FilterOpts) -> Iterable[ObsNight]:
    """
    Find all of the product labels in the directory and convert them
    to product objects
    """
    instruments = [filter_opts.specific_instrument] if filter_opts.specific_instrument else INSTRUMENTS
    return itertools.chain.from_iterable(
        _process_inst_directory(loc, instrument, filter_opts) for instrument in instruments)


def _process_inst_directory(loc: paths.Paths,
                            instrument: str,
                            filter_opts: options.FilterOpts) -> Iterable[ObsNight]:
    """
    Processes the given instrument directory

    Inside of an instrument directory, the labels are organized in subdirectories by year.

    basedir: the absolute path the to the top-level source files
    instrument: the mpc code for the instrument
    """
    logging.info(f"Processing instrument directory: {instrument}")

    instdir = loc.datadir(instrument)
    logging.info(f"processing {instdir}...")
    years = (x.name for x in os.scandir(instdir) if x.is_dir())

    return itertools.chain.from_iterable(
        _process_year_directory(loc, instrument, year, filter_opts) for year in years)


def _process_year_directory(loc: paths.Paths,
                            instrument: str,
                            year: str,
                            filter_opts: options.FilterOpts) -> Iterable[ObsNight]:
    """
    Processes the given year directory.

    Inside of a year directory, the labels are organized in subdirectories by date.

    yeardir: the absolute path to the files for the given year
    instrument: the mpc code of the instrument
    year: the year being processed
    """
    logging.info(f"processing year directory {instrument}/{year}")
    yeardir = loc.datadir(instrument, year)
    days_to_ignore = IGNORE_DATES + build_ignore_dates(filter_opts.ignore_past_days)
    discovered_dates = [x.name for x in os.scandir(yeardir)
                        if x.is_dir() and os.access(x, os.W_OK) and x.name not in days_to_ignore]
    discovered_obsnights = (ObsNight(inst=instrument, year=year, date=d) for d in discovered_dates)
    return [x for x in discovered_obsnights
            if date_has_semaphore(loc, x) and date_has_products(loc, x)]


def build_ignore_dates(num_days: int) -> list[str]:
    """
    Builds a list of days to ignore when processing. This will be the past n days
    """
    deltas = [datetime.timedelta(days=x) for x in range(0, num_days)]
    dates = [datetime.datetime.now() - delta for delta in deltas]
    datestrs = [dt.strftime("%y%b%d") for dt in dates]
    return datestrs


def date_has_semaphore(loc: paths.Paths, night: ObsNight) -> bool:
    datadir = loc.datadir(night.inst, night.year, night.date)
    labeldir = loc.labeldir(night.inst, night.year, night.date)
    return _semaphore_exists(datadir) and _semaphore_exists(labeldir)


def date_has_products(loc: paths.Paths, night: ObsNight) -> bool:
    return _label_dir_has_products(loc.labeldir(night.inst, night.year, night.date))


def _label_dir_has_products(labeldir: str) -> bool:
    return len(_get_labels(labeldir)) > 0


def _semaphore_exists(dirname: str) -> bool:
    """
    Verifies that a semaphore file exists in the given directory.

    dirname: the absolute path of the directory to check
    """
    logging.info(f"checking for semaphore in {dirname}")
    semaphore_file = os.path.join(dirname, '.autoxfer')
    return os.path.exists(semaphore_file)


def _get_labels(labeldir: str) -> list[str]:
    return [x.name for x in os.scandir(labeldir) if _is_label(x)]


def _is_label(candidate: os.DirEntry) -> bool:
    """
    Determines if the given file is a label file.
    """
    return candidate.name.endswith('.xml') and _check_writable(candidate)


def _check_writable(candidate: os.DirEntry) -> bool:
    if os.access(candidate, os.W_OK):
        return True
    return False


def discover_date_products(loc: paths.Paths, night: ObsNight) -> Iterable[Product]:
    """
    Processes the data in a given data directory and label directory pair.

    This checks for a semaphore file before actually doing the processing.

    datadir: the absolute path to the actual data files
    labeldir: the absolute path to the label files
    """
    logging.info(f"processing data directory {night.inst}/{night.year}/{night.date}")

    datadir = loc.datadir(night.inst, night.year, night.date)
    labeldir = loc.labeldir(night.inst, night.year, night.date)
    if _semaphore_exists(datadir) and _semaphore_exists(labeldir):
        return _labels_to_products(datadir, labeldir, night)

    logging.warning(f"no semaphore: {labeldir} and {datadir}")
    return []


def _labels_to_products(datadir: str, labeldir: str, night: ObsNight) -> Iterable[Product]:
    """
    Processes the data in a given data directory and label directory pair.

    datadir: the absolute path to the actual data files
    labeldir: the absolute path to the label files
    """
    logging.info(f"Processing searching for labels in {night.inst}/{night.year}/{night.date}")
    files = _get_labels(labeldir)
    empty_labels = [x for x in files if os.path.getsize(os.path.join(labeldir, x)) == 0]
    if empty_labels:
        logging.warning(f"Empty labels in {labeldir}: {empty_labels}")

    unwritable_labels = [x for x in files if not os.access(os.path.join(labeldir, x), os.W_OK)]
    if unwritable_labels:
        logging.warning(f"Unwritable labels in {labeldir}: {unwritable_labels}")

    usable_labels = [x for x in files if x not in empty_labels and x not in unwritable_labels]

    products = (Product(datadir, os.path.join(labeldir, infile), night) for infile in usable_labels)
    logging.info(f"discovery complete in {night.inst}/{night.year}/{night.date}")
    return products
