"""
Common code for label extraction
"""
import os
import itertools

import bs4


def extract_collection(collection: bs4.Tag) -> dict:
    """
    Extracts keywords from the Product_Collection element
    """
    result = {}
    result.update(extract_identification_area(collection.Identification_Area))
    result.update(extract_context_area(collection.Context_Area))

    return result


def extract_product_observational(product_observational: bs4.Tag) -> dict:
    """
    Extracts keywords from the Product_Observational element
    """
    result = {}
    result.update(extract_identification_area(product_observational.Identification_Area))
    result.update(extract_file_area(product_observational.File_Area_Observational))
    result.update(extract_observation_area(product_observational.Observation_Area))
    if product_observational.Discipline_Area:
        result.update(extract_discipline_area(product_observational.Discipline_Area))
    return result


def extract_product_ancillary(product_ancillary: bs4.Tag) -> dict:
    """
    Extracts keywords from the Product_Observational element
    """
    result = {}
    result.update(extract_identification_area(product_ancillary.Identification_Area))
    result.update(extract_file_area(product_ancillary.File_Area_Ancillary))
    if product_ancillary.Context_Area:
        result.update(extract_context_area(product_ancillary.Context_Area))
    if product_ancillary.Discipline_Area:
        result.update(extract_discipline_area(product_ancillary.Discipline_Area))
    return result


def extract_product_document(product_document: bs4.Tag) -> dict:
    """
    Extracts keywords from the Product_Document element
    """
    result = {}
    result.update(extract_identification_area(product_document.Identification_Area))
    result.update(extract_document(product_document.Document))
    return result


def extract_identification_area(identification_area: bs4.Tag) -> dict:
    """
    Extracts keywords from the Identification_Area element
    """
    lid = str(identification_area.logical_identifier.string)
    vid = str(identification_area.version_id.string)
    modification_history = extract_modification_history(identification_area.Modification_History)

    major, minor = [int(x) for x in vid.split(".")]

    return {
        "logical_id": lid,
        "collection_id": extract_collection_id(lid),
        "version_id": vid,
        "lidvid": f"{lid}::{vid}",
        "major": major,
        "minor": minor,
        "modification_history": modification_history
    }


def extract_modification_history(modification_history: bs4.Tag) -> list[dict]:
    if modification_history:
        return [extract_modification_detail(d) for d in modification_history.find_all("Modification_Detail")]
    return []


def extract_modification_detail(modification_detail: bs4.Tag) -> dict:
    return {
        "version_id": modification_detail.version_id.text,
        "modification_date": modification_detail.modification_date.text,
        "description": modification_detail.description.text
    }


def extract_observation_area(context_area: bs4.Tag) -> dict:
    """
    Extract from the observation_area element
    """
    return extract_time_coordinates(context_area.Time_Coordinates)


def extract_context_area(context_area: bs4.Tag) -> dict:
    """
    Extract from the observation_area element
    """
    result = {}
    if context_area.Time_Coordinates:
        result.update(extract_time_coordinates(context_area.Time_Coordinates))
    return result


def extract_time_coordinates(time_coordinates: bs4.Tag) -> dict:
    """
    gets the start and stop time from the time_coordinates element
    """
    return {
        "start_date": optstr(time_coordinates.start_date_time.string),
        "stop_date": optstr(time_coordinates.stop_date_time.string)
    }


def extract_file_area(file_area: bs4.Tag) -> dict:
    """
    Extracts keywords from the File_Area element
    """
    return {
        "file_name": os.path.basename(str(file_area.File.file_name.string))
    }


def extract_collection_id(lid: str) -> str:
    """
    Extracts the collection id component from a LID
    """
    return lid.split(':')[4]


def extract_discipline_area(discipline_area: bs4.Tag) -> dict:
    """
    Extracts discipline information from the discipline area
    """

    if discipline_area.Processing_Information:
        return extract_processing_information(discipline_area.Processing_Information)
    return {}


def extract_processing_information(processing_information: bs4.Tag) -> dict:
    """
    Extracts information from the processing area
    """
    return {'process': [extract_process(process) for process in processing_information.find_all("Process")]}


def extract_process(process: bs4.Tag) -> dict:
    """
    Extract from the process element
    """
    return {
        'name': str(process.find("name").string) if process.find("name") else '',
        'description': str(process.description.string) if process.description else '',
        'software': [extract_software(software) for software in process.find_all("Software")]
    }


def extract_software(software: bs4.Tag) -> dict:
    """
    Extract from the software element
    """
    return {
        "software_id": str(software.software_id.string) if software.software_id else '', 
        "software_version_id":
            str(software.software_version_id.string) if software.software_version_id is not None else '',
        'software_program': [extract_software_program(software_program)
                             for software_program in software.find_all("Software_Program")]
    }


def extract_software_program(software_program: bs4.Tag) -> dict:
    """
    Extract from the software element
    """
    return {
        "name": str(software_program.find("name").string) if software_program.find("name") else '',
        "program_version":
            str(software_program.program_version.string) if software_program.program_version is not None else ''
    }


def extract_document(document: bs4.Tag) -> dict:
    """
    Extracts keywords form the Document element
    """

    editions = [extract_document_edition(edition) for edition in document.find_all("Document_Edition")]
    return {
        'file_names': list(itertools.chain.from_iterable([edition['file_names'] for edition in editions]))
    }


def extract_document_edition(document_edition: bs4.Tag) -> dict:
    """
    Extracts keywords form the Document_Edition element
    """
    files = [extract_document_file(document_file) for document_file in document_edition.find_all("Document_File")]
    return {
        'file_names': [docfile['filename'] for docfile in files]
    }


def extract_document_file(document_file: bs4.Tag) -> dict:
    """
    Extracts keywords form the Document_File element
    """
    return {
        'filename': str(document_file.file_name.string)
    }


def optstr(value: str) -> str:
    return str(value) if value else None
