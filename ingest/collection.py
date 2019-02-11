'''
This class represents a product, and contains the necessary
attributes for running through the pipeline.
'''
from bs4 import BeautifulSoup

def extract_label(label):
    '''
    Extracts keywords from a PDS4 label.
    '''
    if label.Product_Collection:
        return extract_collection(label.Product_Collection)
    return {}

def extract_collection(collection):
    '''
    Extracts keywords from the Product_Observational element
    '''
    result = {}
    result.update(extract_identification_area(collection.Identification_Area))
    return result

def extract_collection_id(lid):
    '''
    Extracts the collection id component from a LID
    '''
    return lid.split(':')[4]


def extract_identification_area(identification_area):
    '''
    Extracts keywords from the Identification_Area element
    '''
    lid = identification_area.logical_identifier.string
    vid = identification_area.version_id.string
    major, minor = [int(x) for x in vid.split(".")]

    return {
        "logical_id": lid,
        "collection_id": extract_collection_id(lid),
        "version_id": vid,
        "lidvid": lid + "::" + vid,
        "major": major,
        "minor": minor
    }


class Collection:
    '''
    Represents the collection itself
    '''
    def __init__(self, filename):
        '''
        Parses a label file into a Collection
        '''
        with open(filename) as infile:
            label = BeautifulSoup(infile, 'lxml-xml')
            if label:
                self.keywords = extract_label(label)
