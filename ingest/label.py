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
    result.update(extract_discipline_area(product_observational.Discipline_Area))
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
    '''
    Extract from the observation_area element
    '''
    return extract_time_coordinates(context_area.Time_Coordinates)

def extract_time_coordinates(time_coordinates):
    '''
    gets the start and stop time from the time_coordinates element
    '''
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

def extract_discipline_area(discipline_area):
    '''
    Extracts discipline information from the discipline area
    '''

    if discipline_area.Processing_Information:
        return extract_processing_information(discipline_area.Processing_Information)
    return {}

def extract_processing_information(processing_information):
    '''
    Extracts information from the processing area
    '''
    return {'software': [extract_process(process) for process in processing_information.find_all("Process")]}

def extract_process(process):
    '''
    Extract from the process element
    '''
    return extract_software(process.Software)

def extract_software(software):
    '''
    Extract from the software element
    '''
    return {
        "software_id": software.software_id.string if software.software_id else '', 
        "software_version_id": software.software_version_id.string if software.software_version_id else ''
    }
