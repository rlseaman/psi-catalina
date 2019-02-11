'''
This class represents a product, and contains the necessary
attributes for running through the pipeline.
'''
import os
from bs4 import BeautifulSoup

def extract_label(label):
    '''
    Extracts keywords from a PDS4 label.
    '''
    if label.Product_Observational:
        return extract_product_observational(label.Product_Observational)
    return {}

def extract_product_observational(product_observational):
    '''
    Extracts keywords from the Product_Observational element
    '''
    result = {}
    result.update(extract_identification_area(product_observational.Identification_Area))
    result.update(extract_file_area(product_observational.File_Area_Observational))
    return result

def extract_identification_area(identification_area):
    '''
    Extracts keywords from the Identification_Area element
    '''
    lid = identification_area.logical_identifier.string
    vid = identification_area.version_id.string
    return {
        "logical_id": lid,
        "collection_id": extract_collection_id(lid),
        "version_id": vid,
        "lidvid": lid + "::" + vid
    }

def extract_file_area(file_area):
    '''
    Extracts keywords from the File_Area element
    '''
    return {
        "file_name": os.path.basename(file_area.File.file_name.string)
    }

def extract_collection_id(lid):
    '''
    Extracts the collection id component from a LID
    '''
    return lid.split(':')[4]


class Product:
    '''
    Represents the product itself.
    '''

    def __init__(self, filename, inst, year, date):
        '''
        Parses a label file into a Product
        '''
        with open(filename) as infile:
            label = BeautifulSoup(infile, 'lxml-xml')
            if label:
                self.keywords = extract_label(label)
                self.inst = inst
                self.year = year
                self.date = date
                self.labelfilename = filename
