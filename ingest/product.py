'''
This class represents a product, and contains the necessary
attributes for running through the pipeline.
'''
import os
from bs4 import BeautifulSoup
import label
import logging


def extract_label(xmldoc, filepath=''):
    '''
    Extracts keywords from a PDS4 label.
    '''
    if xmldoc.Product_Observational:
        return label.extract_product_observational(xmldoc.Product_Observational)
    if xmldoc.Product_Ancillary:
        return label.extract_product_ancillary(xmldoc.Product_Ancillary)
    if xmldoc.Product_Document:
        return label.extract_product_document(xmldoc.Product_Document)

    raise RuntimeError(f"Unknown product type: {filepath}" )
    

def extract_keywords(infile, filepath=''):
    '''
    Wrapper for extract_label. This handles creation and destruction of
    the BeautifulSoup object.
    '''
    xmldoc = BeautifulSoup(infile, 'lxml-xml')
    if xmldoc:
        keywords = extract_label(xmldoc, filepath)
        xmldoc.decompose()
        return keywords
    else:
        raise RuntimeError(f"Not a valid xml document: {filepath}")


class Product:
    '''
    Represents the product itself.
    '''

    def __init__(self, datadir, filepath, inst=None, year=None, date=None):
        '''
        Parses a label file into a Product
        '''
        logging.debug(f"Creating product for: {filepath}")
        with open(filepath) as infile:
            self.keywords = extract_keywords(infile, filepath)
            self.inst = inst
            self.year = year
            self.date = date
            self.labelfilename = os.path.basename(filepath)
            self.labeldir = os.path.dirname(filepath)
            self.labelpath = filepath
            self.datadir = datadir

    def lidvid(self):
        return self.keywords['lidvid']

    def filenames(self):
        return self.keywords['file_names'] if 'file_names' in self.keywords else [self.keywords['file_name']]

    def start_date(self):
        return self.keywords.get('start_date')

    def stop_date(self):
        return self.keywords.get('stop_date')

    def majorversion(self):
        return self.keywords.get('majorversion')

    def minorversion(self):
        return self.keywords.get('minorversion')

    def collection_id(self):
        return self.keywords.get('collection_id')

    def software(self):
        return self.keywords.get('software')
