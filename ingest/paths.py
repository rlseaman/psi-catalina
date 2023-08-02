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

    def datadir(self, inst: str = None, year: str = None, date: str = None, filename: str = None) -> str:
        """
        Returns the data directory
        """
        return self._buildpath((self.basedir, inst, year, date, filename))

    def labeldir(self, inst: str = None, year: str = None, date: str = None, filename: str = None) -> str:
        """
        Returns the label file directory
        """
        subdir = "other/pds4" if date else None
        return self._buildpath((self.basedir, inst, year, subdir, date, filename))

    def destdir(self,
                collection_id: Optional[str],
                inst: str = None,
                year: str = None,
                sub_dir: str = None,
                date: str = None,
                failed: bool = False) -> str:
        """
        Returns the destination directory
        """
        if failed:
            elements = [x for x in [self.failure_dir, collection_id, inst, year, date] if x is not None]
            return self._buildpath(elements)
        else:
            elements = [x for x in [self.validated_dir, collection_id, inst, year, sub_dir, date] if x is not None]
            return self._buildpath(elements)

    def product_dest_dir(self, p: product.Product, failed: bool = False) -> str:
        return self.destdir(p.collection_id(), p.night.inst, p.night.year, None, p.night.date, failed)

    def validation_data_dir(self, p: product.Product, failed: bool = False) -> str:
        return self.destdir(None, p.night.inst, p.night.year, None, p.night.date, failed)

    def night_validation_data_dir(self, inst: str, year: str, date: str, failed=False) -> str:
        return self.destdir(None, inst, year, None, date, failed)        

    def validation_label_dir(self, p: product.Product, failed: bool = False) -> str:
        return self.destdir(None, p.night.inst, p.night.year, "other/pds4", p.night.date, failed)

    def night_validation_label_dir(self, inst: str, year: str, date: str, failed: bool = False) -> str:
        return self.destdir(None, inst, year, "other/pds4", date, failed)        

    def _buildpath(self, elements: Iterable[str]) -> str:
        return os.path.join(*self._filled_elements(elements))

    @staticmethod
    def _filled_elements(elements: Iterable[str]) -> list[str]:
        element_list = list(elements)
        if any(itertools.dropwhile(lambda x: x, element_list)):
            raise Exception("Gaps detected in path:", element_list)
        return list(itertools.takewhile(lambda x: x, element_list))
