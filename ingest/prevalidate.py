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
            logging.warning(f'Product {candidate.labelfilename} failed prevalidation: {"; ".join(errors)}')
        else:
            yield candidate


def prevalidate(candidate: product.Product) -> list[str]:
    result = []
    if not date_is_present(candidate):
        result.append("Product is missing a date.")
    result.extend(check_observation_area(candidate))
    result.extend(match_collection_and_file_type(candidate))
    return result


def date_is_present(candidate: product.Product) -> bool:
    if date_required(candidate):
        return not (candidate.start_date() is None or candidate.stop_date() is None)
    return True


def date_required(candidate: product.Product) -> bool:
    if candidate.collection_id() == 'calibration':
        return False
    return any(is_image(datafile) for datafile in candidate.filenames())


def is_image(datafile):
    return any(datafile.endswith(extension) for extension in IMAGE_EXTENSIONS)


def check_observation_area(candidate: product.Product) -> Iterable[str]:
    for component in candidate.observing_system_components():
        if component.name is None:
            yield f'{component.type} observing system component has no name'
        if component.internal_reference and component.internal_reference.lid_reference is None:
            yield f'{component.type} observing system component has an empty lid'


def match_collection_and_file_type(candidate: product.Product) -> Iterable[str]:
    collection_id = candidate.collection_id()
    for filename in candidate.filenames():
        _, extension = os.path.splitext(filename)

        if not (extension in COLLECTION_EXTENSIONS.get(collection_id, [])
                or any(re.match(f'^{pattern}$', filename) for pattern in COLLECTION_REGEXES.get(collection_id, []))):
            yield f'{filename} in {candidate.labelfilename} is not suitable for the {collection_id} collection'
