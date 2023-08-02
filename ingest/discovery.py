import datetime
import itertools
import logging
import os
from typing import Iterable

import options
import paths


def discover_product_dirs(loc: paths.Paths, filter_opts: options.FilterOpts) -> Iterable[tuple[str, str, str]]:
    """
    Find all of the product labels in the directory and convert them
    to product objects
    """
    instruments = [filter_opts.specific_instrument] if filter_opts.specific_instrument else INSTRUMENTS
    return itertools.chain.from_iterable(
        process_inst_directory(loc, instrument, filter_opts) for instrument in instruments)


INSTRUMENTS = ['703', 'G96', 'I52', 'V06']


def process_inst_directory(loc: paths.Paths,
                           instrument: str,
                           filter_opts: options.FilterOpts) -> Iterable[tuple[str, str, str]]:
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
        process_year_directory(loc, instrument, year, filter_opts) for year in years)


def process_year_directory(loc: paths.Paths,
                           instrument: str,
                           year: str,
                           filter_opts: options.FilterOpts) -> Iterable[tuple[str, str, str]]:
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
    return [(instrument, year, d) for d in discovered_dates
            if date_has_semaphore(loc, instrument, year, d) and date_has_products(loc, instrument, year, d)]


IGNORE_DATES = ['pds4', 'other']


def build_ignore_dates(num_days: int) -> list[str]:
    """
    Builds a list of days to ignore when processing. This will be the past n days
    """
    deltas = [datetime.timedelta(days=x) for x in range(0, num_days)]
    dates = [datetime.datetime.now() - delta for delta in deltas]
    datestrs = [dt.strftime("%y%b%d") for dt in dates]
    return datestrs


def date_has_semaphore(loc: paths.Paths, instrument: str, year: str, date: str) -> bool:
    datadir = loc.datadir(instrument, year, date)
    labeldir = loc.labeldir(instrument, year, date)
    return semaphore_exists(datadir) and semaphore_exists(labeldir)


def date_has_products(loc: paths.Paths, instrument: str, year: str, date: str) -> bool:
    return label_dir_has_products(loc.labeldir(instrument, year, date))


def label_dir_has_products(labeldir: str) -> bool:
    return len(get_labels(labeldir)) > 0


def semaphore_exists(dirname: str) -> bool:
    """
    Verifies that a semaphore file exists in the given directory.

    dirname: the absolute path of the directory to check
    """
    logging.info(f"checking for semaphore in {dirname}")
    semaphore_file = os.path.join(dirname, '.autoxfer')
    return os.path.exists(semaphore_file)


def get_labels(labeldir: str) -> list[str]:
    return [x.name for x in os.scandir(labeldir) if is_label(x)]


def is_label(candidate: os.DirEntry) -> bool:
    """
    Determines if the given file is a label file.
    """
    return candidate.name.endswith('.xml') and check_writable(candidate)


def check_writable(candidate: os.DirEntry) -> bool:
    if os.access(candidate, os.W_OK):
        return True
    return False
