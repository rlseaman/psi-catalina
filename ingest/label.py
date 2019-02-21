'''
Common code for label extraction
'''
import os

def extract_collection(collection):
    '''
    Extracts keywords from the Product_Observational element
    '''
    result = {}
    result.update(extract_identification_area(collection.Identification_Area))
    return result

def extract_product_observational(product_observational):
    '''
    Extracts keywords from the Product_Observational element
    '''
    result = {}
    result.update(extract_identification_area(product_observational.Identification_Area))
    result.update(extract_file_area(product_observational.File_Area_Observational))
    result.update(extract_observation_area(product_observational.Observation_Area))
    return result

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

def extract_observation_area(context_area):
    return extract_time_coordinates(context_area.Time_Coordinates)

def extract_time_coordinates(time_coordinates):
    return {
        "start_date": time_coordinates.start_date_time.string,
        "stop_date": time_coordinates.stop_date_time.string
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
