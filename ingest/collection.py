"""
This class represents a product, and contains the necessary
attributes for running through the pipeline.
"""
from typing import Optional

from bs4 import BeautifulSoup
import label
import os

from pds4types import CollectionLabel, ModificationHistory


def extract_label(xmldoc: BeautifulSoup) -> Optional[CollectionLabel]:
    """
    Extracts keywords from a PDS4 label.
    """
    if xmldoc.Product_Collection:
        return label.extract_collection(xmldoc.Product_Collection)
    return None


class Collection:
    """
    Represents the collection itself
    """
    def __init__(self, collection_path: str, filename: str) -> None:
        """
        Parses a label file into a Collection
        """
        filepath = os.path.join(collection_path, filename)
        with open(filepath) as infile:
            xmldoc = BeautifulSoup(infile, 'lxml-xml')
            if xmldoc:
                self.keywords = extract_label(xmldoc)

    def start_date(self) -> str:
        """
        Retrieves the start date of the collection
        """
        return self.keywords.context_area.time_coordinates.start_date

    def stop_date(self) -> str:
        """
        Retrieves the stop date of the collection
        """
        return self.keywords.context_area.time_coordinates.stop_date

    def majorversion(self) -> int:
        """
        Retrieves the major version of the collection
        """
        return self.keywords.identification_area.major

    def minorversion(self) -> int:
        """
        Retrieves the minor of the collection
        """
        return self.keywords.identification_area.minor

    def modification_history(self) -> ModificationHistory:
        return self.keywords.identification_area.modification_history
