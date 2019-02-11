'''
This class represents a product, and contains the necessary
attributes for running through the pipeline.
'''
from bs4 import BeautifulSoup
import label
import os

def extract_label(xmldoc):
    '''
    Extracts keywords from a PDS4 label.
    '''
    if xmldoc.Product_Collection:
        return label.extract_collection(xmldoc.Product_Collection)
    return {}

class Collection:
    '''
    Represents the collection itself
    '''
    def __init__(self, collection_path, filename):
        '''
        Parses a label file into a Collection
        '''
        filepath = os.path.join(collection_path, filename)
        with open(filepath) as infile:
            xmldoc = BeautifulSoup(infile, 'lxml-xml')
            if xmldoc:
                self.keywords = extract_label(xmldoc)
