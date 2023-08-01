import logging
import os.path
import re

import product
from typing import Iterable

IMAGE_EXTENSIONS = ['.fits', '.calb', '.pass1', '.csub', '.avgs', '.avgr', '.arch']

COLLECTION_EXTENSIONS = {
    'calibration': [],
    'data_raw': ['.fits'],
    'data_partially_processed': ['.calb', '.pass1', '.csub', '.avgs', '.avgr'],
    'data_calibrated': ['.arch'],
    'data_derived': ['.sext', '.sexb', '.sexs', '.mtds', '.mtdf', '.dets', '.rjct', '.mpcd', '.neos', '.fail',
                     '.tssexb', '.avgrsexb', '.detf'],
    'miscellaneous': ['.detl', '.detb', '.iext', '.strp', '.strm', '.scmp', '.ephm', '.achk', '.hits', '.arch_h',
                      '.ast', '.mrpt', '.ades', '.focheck', '.param', '.params', '.outparams', '.json',
                      '.log', '.point', '.pt', '.xmls', '.cov', '.txt']
}

COLLECTION_REGEXES = {
    'calibration': [r'.*flat.*\.fits'],
    'data_raw': [r'.*\.fits_.*'],
    'data_partially_processed': [],
    'data_calibrated': [],
    'data_derived': [],
    'miscellaneous': [r'MPCORB\.DAT', r'mpcorb\.sof', r'ELEMENTS\.COMET', r'ObsCodes\.html', r'signature\.md5']
}


def prevalidate_products(products: Iterable[product.Product]) -> Iterable[product.Product]:
    for candidate in products:
        errors = prevalidate(candidate)
        if len(errors) > 0:
            message = "\n\t" + "\n\t".join(errors)
            logging.warning(f'Product {candidate.labelfilename} failed prevalidation: {message}')
        else:
            yield candidate


def prevalidate(candidate: product.Product) -> list[str]:
    result = []
    result.extend(check_dates(candidate))
    result.extend(check_observation_area(candidate))
    result.extend(match_collection_and_file_type(candidate))
    return result


def check_dates(candidate: product.Product) -> Iterable[str]:
    if date_required(candidate):
        if candidate.start_date() is None:
            yield 'Product is missing a start date'
        if candidate.stop_date() is None:
            yield 'Product is missing an end date'


def date_required(candidate: product.Product) -> bool:
    if candidate.collection_id() == 'calibration':
        return False
    return any(is_image(datafile) for datafile in candidate.filenames())


def is_image(datafile: str) -> bool:
    _, extension = os.path.splitext(datafile)
    return extension in IMAGE_EXTENSIONS


def check_observation_area(candidate: product.Product) -> Iterable[str]:
    for component in candidate.observing_system_components():
        if component.name is None:
            yield f'{component.type} observing system component has no name'
        if component.internal_reference and component.internal_reference.lid_reference is None:
            yield f'{component.type} observing system component has an empty lid'


def match_collection_and_file_type(candidate: product.Product) -> Iterable[str]:
    collection_id = candidate.collection_id()

    if collection_id in COLLECTION_EXTENSIONS.keys():
        for filename in candidate.filenames():
            _, extension = os.path.splitext(filename)

            if not (extension_matches_collection(collection_id, extension)
                    or filename_matches_collection(collection_id, filename)):
                yield f'{filename} is not suitable for the {collection_id} collection'
    else:
        yield f'collection {collection_id} not recognized'


def filename_matches_collection(collection_id: str, filename: str) -> bool:
    return any(re.match(f'^{pattern}$', filename) for pattern in COLLECTION_REGEXES.get(collection_id, []))


def extension_matches_collection(collection_id: str, extension: str) -> bool:
    return extension in COLLECTION_EXTENSIONS.get(collection_id, [])
