import product

IMAGE_EXTENSIONS = ['.fits', '.calb', '.pass1', '.csub', '.avgs', '.avgr', '.arch']


def prevalidate(candidate: product.Product) -> list[str]:
    result = []
    if not date_is_present(candidate):
        result.extend("Product is missing a date.")
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
