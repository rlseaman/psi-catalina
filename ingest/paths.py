import os
import itertools
from typing import Iterable, Optional

import options
import product


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
            else self._buildpath((self.dest, "failed"))
        self.validated_dir = location_opts.validated_dir \
            if location_opts.validated_dir \
            else self._buildpath((self.dest, self.bundle_id))

    def partialdir(self, inst: str, year: str = None) -> str:
        """
        Used during initial discovery before a complete observation night is constructed. This will return
        either the directory for an instrument, or the directory for the year underneath the instrument, if a year is
        provided.

        This will be in the form: BASE/INST/YEAR
        """
        return self._buildpath((self.basedir, inst, year))

    def datadir(self, night: product.ObsNight, filename: str = None) -> str:
        """
        Returns the data directory for an observation night. It can also return the location of an individual
        file in this directory, if a filename is provided.

        This will be in the form: BASE/INST/YEAR/DATE/FILE
        """
        return self._buildpath((self.basedir, night.inst, night.year, night.date, filename))

    def labeldir(self, night: product.ObsNight, filename: str = None) -> str:
        """
        Returns the label directory for an observation night. This is different from the data directory, and it is
        in a nearby directory, instead of directly underneath the data directory.  It can also return the location of
        an individual file in this directory, if a filename is provided.

        This will be in the form: BASE/INST/YEAR/other/pds4/DATE/FILE
        """
        subdir = "other/pds4" if night else None
        return self._buildpath((self.basedir, night.inst, night.year, subdir, night.date, filename))

    def _destdir(self,
                 collection_id: Optional[str] = None,
                 night: product.ObsNight = None,
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
                                    night.inst if night else None,
                                    night.year if night else None,
                                    night.date if night else None] if x is not None]
            return self._buildpath(elements)
        else:
            elements = [x for x in [self.validated_dir,
                                    collection_id,
                                    night.inst if night else None,
                                    night.year if night else None,
                                    sub_dir,
                                    night.date if night else None] if x is not None]
            return self._buildpath(elements)

    def collection_dir(self, collection_id: str) -> str:
        """ Returns the destination directory for generated collection files. """
        return self._destdir(collection_id=collection_id, failed=False)

    def product_dest_dir(self, p: product.Product, failed: bool) -> str:
        """ Returns the destination directory for fully processed products """
        return self._destdir(collection_id=p.collection_id(), night=p.night, failed=failed)

    def validation_data_dir(self, night: product.ObsNight, failed=False) -> str:
        """
        Returns the destination data directory for products that have completed prevalidation, but are not fully
        processed.
        """
        return self._destdir(night=night, failed=failed)

    def validation_label_dir(self, night: product.ObsNight, failed: bool = False) -> str:
        """
        Returns the destination label directory for products that have completed prevalidation, but are not fully
        processed. This mimics the directory structure for incoming files.
        """
        return self._destdir(night=night, sub_dir="other/pds4", failed=failed)

    def _buildpath(self, elements: Iterable[str]) -> str:
        return os.path.join(*self._filled_elements(elements))

    @staticmethod
    def _filled_elements(elements: Iterable[str]) -> list[str]:
        element_list = list(elements)
        if any(itertools.dropwhile(lambda x: x, element_list)):
            raise Exception("Gaps detected in path:", element_list)
        return list(itertools.takewhile(lambda x: x, element_list))
