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

    def partialdir(self, inst: str = None, year: str = None) -> str:
        """
        Returns the data directory
        """
        return self._buildpath((self.basedir, inst, year))

    def datadir(self, night: product.ObsNight, filename: str = None) -> str:
        """
        Returns the data directory
        """
        return self._buildpath((self.basedir, night.inst, night.year, night.date, filename))

    def labeldir(self, night: product.ObsNight = None, filename: str = None) -> str:
        """
        Returns the label file directory
        """
        subdir = "other/pds4" if night else None
        return self._buildpath((self.basedir, night.inst, night.year, subdir, night.date, filename))

    def destdir(self,
                collection_id: Optional[str],
                night: product.ObsNight = None,
                sub_dir: str = None,
                failed: bool = False) -> str:
        """
        Returns the destination directory
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

    def product_dest_dir(self, p: product.Product, failed: bool = False) -> str:
        return self.destdir(p.collection_id(), p.night, None, failed)

    def validation_data_dir(self, p: product.Product, failed: bool = False) -> str:
        return self.destdir(None, p.night, None, failed)

    def night_validation_data_dir(self, night: product.ObsNight, failed=False) -> str:
        return self.destdir(None, night, None, failed)

    def validation_label_dir(self, p: product.Product, failed: bool = False) -> str:
        return self.destdir(None, p.night, "other/pds4", failed)

    def night_validation_label_dir(self, night: product.ObsNight, failed: bool = False) -> str:
        return self.destdir(None, night, "other/pds4", failed)

    def _buildpath(self, elements: Iterable[str]) -> str:
        return os.path.join(*self._filled_elements(elements))

    @staticmethod
    def _filled_elements(elements: Iterable[str]) -> list[str]:
        element_list = list(elements)
        if any(itertools.dropwhile(lambda x: x, element_list)):
            raise Exception("Gaps detected in path:", element_list)
        return list(itertools.takewhile(lambda x: x, element_list))
