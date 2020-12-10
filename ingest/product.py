'''
This class represents a product, and contains the necessary
attributes for running through the pipeline.
'''
import os
from bs4 import BeautifulSoup
import label
import logging

def extract_label(xmldoc):
    '''
    Extracts keywords from a PDS4 label.
    '''
    if xmldoc.Product_Observational:
        return label.extract_product_observational(xmldoc.Product_Observational)
    if xmldoc.Product_Document:
        return label.extract_product_document(xmldoc.Product_Document)

    print ("Unknown product type")
    return {}

class Product:
    '''
    Represents the product itself.
    '''

    def __init__(self, datadir, filepath, inst=None, year=None, date=None):
        '''
        Parses a label file into a Product
        '''
        logging.debug("Creating product for: %s", filepath)
        with open(filepath) as infile:
            xmldoc = BeautifulSoup(infile, 'lxml-xml')
            if xmldoc:
                keywords = extract_label(xmldoc)
                if 'lidvid' not in keywords:
                    raise Exception("no lidvid in file:" + filepath)
                self.lidvid = keywords['lidvid']
                self.filenames = keywords['file_names'] if 'file_names' in keywords else [keywords['file_name']]
                self.start_date = keywords.get('start_date')
                self.stop_date = keywords.get('stop_date')
                self.majorversion = keywords.get('major')
                self.minorversion = keywords.get('minor')
                self.collection_id = keywords.get('collection_id')
                self.software = keywords.get('software')

                self.inst = inst
                self.year = year
                self.date = date
                self.labelfilename = os.path.basename(filepath)
                self.labeldir = os.path.dirname(filepath)
                self.labelpath = filepath
                self.datadir = datadir

