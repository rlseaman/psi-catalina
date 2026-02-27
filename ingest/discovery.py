from __future__ import annotations
import datetime
import itertools
import logging
import os
from typing import Iterable

import options
import paths
from product import Product, ObsNight

IGNORE_DATES = ['pds4', 'other']
INSTRUMENTS = ['703', 'G96', 'I52', 'V06']


class Discovery:
    def __init__(self, loc: paths.Paths, filter_opts: options.FilterOpts) -> None:
        self.loc = loc
        self.filter_opts = filter_opts

    def discover_product_dirs(self) -> Iterable[ObsNight]:
        """
        Find all of the product labels in the directory and convert them
        to product objects
        """
        instruments = [self.filter_opts.specific_instrument] if self.filter_opts.specific_instrument else INSTRUMENTS
        return itertools.chain.from_iterable(
            self._process_inst_directory(instrument) for instrument in instruments)

    def _process_inst_directory(self, instrument: str) -> Iterable[ObsNight]:
        """
        Processes the given instrument directory

        Inside of an instrument directory, the labels are organized in subdirectories by year.

        basedir: the absolute path the to the top-level source files
        instrument: the mpc code for the instrument
        """
        logging.info(f"Processing instrument directory: {instrument}")

        instdir = self.loc.partialdir(instrument)
        logging.info(f"processing {instdir}...")
        years = (x.name for x in os.scandir(instdir) if x.is_dir())

        return itertools.chain.from_iterable(
            self._process_year_directory(instrument, year) for year in years)

    def _process_year_directory(self,
                                instrument: str,
                                year: str,
                                ) -> Iterable[ObsNight]:
        """
        Processes the given year directory.

        Inside of a year directory, the labels are organized in subdirectories by date.

        yeardir: the absolute path to the files for the given year
        instrument: the mpc code of the instrument
        year: the year being processed
        """
        logging.info(f"processing year directory {instrument}/{year}")
        yeardir = self.loc.partialdir(instrument, year)
        days_to_ignore = IGNORE_DATES + self.build_ignore_dates(self.filter_opts.ignore_past_days)
        discovered_dates = [x.name for x in os.scandir(yeardir)
                            if x.is_dir() and os.access(x, os.W_OK) and x.name not in days_to_ignore]
        discovered_obsnights = (ObsNight(inst=instrument, year=year, date=d) for d in discovered_dates)
        return [x for x in discovered_obsnights
                if self.date_has_semaphore(x) and self.date_has_products(x)]

    def date_has_semaphore(self, night: ObsNight) -> bool:
        night_loc = self.loc.fornight(night)
        datadir = night_loc.datadir()
        labeldir = night_loc.labeldir()
        return self._semaphore_exists(datadir) and self._semaphore_exists(labeldir)

    def date_has_products(self, night: ObsNight) -> bool:
        """
        Determines if there are products available for an observation night
        @param night:
        @return:
        """
        return self._label_dir_has_products(self.loc.fornight(night).labeldir())

    def _label_dir_has_products(self, labeldir: str) -> bool:
        """
        Determines if there are any labels in a directory.
        @param labeldir: The directory to search
        @return: True if there are any label files in the directory, false otherwise
        """
        return len(self._get_labels(labeldir)) > 0

    @staticmethod
    def _semaphore_exists(dirname: str) -> bool:
        """
        Verifies that a semaphore file exists in the given directory.

        @param dirname: the absolute path of the directory to check
        @return: True if the semaphore file exists, false otherwise
        """
        logging.info(f"checking for semaphore in {dirname}")
        semaphore_file = os.path.join(dirname, '.autoxfer')
        return os.path.exists(semaphore_file)

    def _get_labels(self, label_dir: str) -> list[str]:
        """
        Finds the labels in a directory
        @param label_dir: The directory to search
        @return: A list of label filenames
        """
        return [x.name for x in os.scandir(label_dir) if self._is_label(x)]

    def _is_label(self, candidate: os.DirEntry) -> bool:
        """
        Determines if the given file is a label file. This is kind of a loose test, just making sure that the files are
        xml files. Any actual parsing would be way slower.
        """
        return candidate.name.endswith('.xml') and self._check_writable(candidate)

    @staticmethod
    def _check_writable(candidate: os.DirEntry) -> bool:
        if os.access(candidate, os.W_OK):
            return True
        return False

    def discover_date_products(self, night: ObsNight) -> Iterable[Product]:
        """
        Processes the data in a given data directory and label directory pair.

        This checks for a semaphore file before actually doing the processing.

        @param night: The observation night to search for
        @return: A list of products for the observation night.
        """
        logging.info(f"processing data directory {night.inst}/{night.year}/{night.date}")
        night_loc = self.loc.fornight(night)
        datadir = night_loc.datadir()
        labeldir = night_loc.labeldir()
        if self._semaphore_exists(datadir) and self._semaphore_exists(labeldir):
            return self._labels_to_products(datadir, labeldir, night)

        logging.warning(f"no semaphore: {labeldir} and {datadir}")
        return []

    def _labels_to_products(self, datadir: str, labeldir: str, night: ObsNight) -> Iterable[Product]:
        """
        Processes the data in a given data directory and label directory pair.

        @param datadir: The directory containing the data files
        @param labeldir: The directory containing the label files
        @param night: The observation night to search for
        @return: A list of products for the observation night
        """
        logging.info(f"Processing searching for labels in {night.inst}/{night.year}/{night.date}")
        files = self._get_labels(labeldir)
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

    @staticmethod
    def build_ignore_dates(num_days: int) -> list[str]:
        """
        Builds a list of days to ignore when processing. This will be the past n days
        """
        deltas = [datetime.timedelta(days=x) for x in range(0, num_days)]
        dates = [datetime.datetime.now() - delta for delta in deltas]
        datestrs = [dt.strftime("%y%b%d") for dt in dates]
        return datestrs
