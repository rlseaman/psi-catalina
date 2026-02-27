from __future__ import annotations
import os
import itertools
from typing import Iterable, Optional

import options
import product


class ObsNightLoc:
    def __init__(self, basedir: str, validated_dir: str, failure_dir: str, night: product.ObsNight) -> None:
        self.basedir = basedir
        self.failure_dir = failure_dir
        self.validated_dir = validated_dir
        self.night = night

    def validation_data_dir(self, failed=False) -> str:
        """
        Returns the destination data directory for products that have completed prevalidation, but are not fully
        processed.
        """
        return self._build_dir(failed=failed)

    def validation_label_dir(self, failed: bool = False) -> str:
        """
        Returns the destination label directory for products that have completed prevalidation, but are not fully
        processed. This mimics the directory structure for incoming files.
        """
        return self._build_dir(sub_dir="other/pds4", failed=failed)

    def datadir(self) -> str:
        """
        Returns the data directory for an observation night. It can also return the location of an individual
        file in this directory, if a filename is provided.

        This will be in the form: BASE/INST/YEAR/DATE/FILE
        """
        return os.path.join(self.basedir, self.night.inst, self.night.year, self.night.date)

    def labeldir(self) -> str:
        """
        Returns the label directory for an observation night. This is different from the data directory, and it is
        in a nearby directory, instead of directly underneath the data directory.  It can also return the location of
        an individual file in this directory, if a filename is provided.

        This will be in the form: BASE/INST/YEAR/other/pds4/DATE/FILE
        """
        subdir = "other/pds4"
        return os.path.join(self.basedir, self.night.inst, self.night.year, subdir, self.night.date)

    def dest_dir(self, collection_id: str, failed: bool) -> str:
        """ Returns the destination directory for fully processed products """
        return self._build_dir(collection_id=collection_id, failed=failed)

    def _build_dir(self,
                   collection_id: Optional[str] = None,
                   sub_dir: str = None,
                   failed: bool = False) -> str:
        """
        Returns the destination directory. This can produce a variety of results, based on the options. It can locate
        the destination directory for failed validations, the destination directory for successful files, the
        directory for prevalidated files, and the directory for incoming files.
        """
        if failed:
            elements = [x for x in [self.failure_dir,
                                    collection_id,
                                    self.night.inst,
                                    self.night.year,
                                    self.night.date] if x is not None]
            return _buildpath(elements)
        else:
            elements = [x for x in [self.validated_dir,
                                    collection_id,
                                    self.night.inst,
                                    self.night.year,
                                    sub_dir,
                                    self.night.date] if x is not None]
            return _buildpath(elements)


class Paths:
    """
    A helper class that determines where data files and labels are stored. This
    provides multiple ways to get at each data file and label file, and
    accounts for the fact that the data and labels are delivered in separate locations.
    """
    def __init__(self, location_opts: options.LocationOpts, bundle_id: str) -> None:
        self.basedir = location_opts.basedir
        self.dest = location_opts.destdir
        self.bundle_id = bundle_id
        self.schemadir = location_opts.schemadir
        self.failure_dir = location_opts.failure_dir \
            if location_opts.failure_dir \
            else os.path.join(self.dest, "failed")
        self.validated_dir = location_opts.validated_dir \
            if location_opts.validated_dir \
            else os.path.join(self.dest, self.bundle_id)

    def partialdir(self, inst: str, year: str = None) -> str:
        """
        Used during initial discovery before a complete observation night is constructed. This will return
        either the directory for an instrument, or the directory for the year underneath the instrument, if a year is
        provided.

        This will be in the form: BASE/INST/YEAR
        """
        if year:
            return os.path.join(self.basedir, inst, year)
        else:
            return os.path.join(self.basedir, inst)

    def collection_dir(self, collection_id: str) -> str:
        """ Returns the destination directory for generated collection files. """
        return os.path.join(self.validated_dir, collection_id)

    def product_dest_dir(self, p: product.Product, failed: bool) -> str:
        """ Returns the destination directory for fully processed products """
        return self.fornight(p.night).dest_dir(collection_id=p.collection_id(), failed=failed)

    def fornight(self, night: product.ObsNight) -> ObsNightLoc:
        return ObsNightLoc(basedir=self.basedir,
                           validated_dir=self.validated_dir,
                           failure_dir=self.failure_dir,
                           night=night)


def _buildpath(elements: Iterable[str]) -> str:
    return os.path.join(*_filled_elements(elements))


def _filled_elements(elements: Iterable[str]) -> list[str]:
    element_list = list(elements)
    if any(itertools.dropwhile(lambda x: x, element_list)):
        raise Exception("Gaps detected in path:", element_list)
    return list(itertools.takewhile(lambda x: x, element_list))
