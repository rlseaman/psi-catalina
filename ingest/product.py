'''
This class represents a product, and contains the necessary
attributes for running through the pipeline.
'''
import os
from bs4 import BeautifulSoup
import label

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

    def __init__(self, filepath, inst=None, year=None, date=None):
        '''
        Parses a label file into a Product
        '''
        with open(filepath) as infile:
            xmldoc = BeautifulSoup(infile, 'lxml-xml')
            if xmldoc:
                self.keywords = extract_label(xmldoc)
                self.inst = inst
                self.year = year
                self.date = date
                self.labelfilename = os.path.basename(filepath)
                if 'lidvid' not in self.keywords:
                    raise Exception("no lidvid in file:" + filepath)
