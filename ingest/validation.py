'''
Performs validation on a PDS4 label
'''
from json.decoder import JSONDecodeError
import subprocess
import os.path
import json
import product
import tempfile
import shutil
import gzip
import logging
import re


DICTIONARIES = ['PDS4_IMG_1900',
                'PDS4_DISP_1900',
                'PDS4_GEOM_1900_1510',
                'PDS4_SURVEY_1A00_1000',
                'PDS4_PROC_1900',
                'PDS4_PDS_1A00']


VALIDATE_CMD='validate'
FUNPACK_CMD='funpack'

def validate_product(product, schema_path, skip_data):
    '''
    Moves the entirety of the product to a temporary location,
    decompressed the data files if needed, and validates the product.
    '''
    return validate_products([product], schema_path, skip_data)

def validate_products(products, schema_path, skip_data):
    '''
    Moves the entirety of the product to a temporary location,
    decompressed the data files if needed, and validates the product.
    '''
    with tempfile.TemporaryDirectory() as temp:
        logging.info("Validating products at: %s", temp)
        temp_dir = temp
        for product in products:
            create_temp_copy(temp_dir, product, skip_data)

        return run_validator(temp_dir, schema_path, skip_data)


def create_temp_copy(temp_dir, product, skip_data):
    '''
    Creates temporary copies of the files for a product. Temporary copies are
    needed because the real copies are compressed, and the labels also need
    to be copied so that they can be modified to point to these copies.

    The labels are not changed in place because they should not be changed
    until they are validated.

    If data validation is being skipped, this will still create an empty
    dummy file, so that the validator will not fail.
    '''
    label_file_name = product.labelfilename
    label_path = product.labelpath
    data_dir = product.datadir

    logging.info("Creating temporary copies of %s", label_file_name)

    temp_label_path = os.path.join(temp_dir, label_file_name)
    shutil.copy(label_path, temp_label_path)

    data_file_names = product.filenames()
    for data_file_name in data_file_names:
        data_path = os.path.join(data_dir, data_file_name)
        temp_data_path = os.path.join(temp_dir, data_file_name)

        if skip_data:
            logging.debug("Creating dummy copy of %s", data_path)
            with open(temp_data_path, "w") as f: pass
        elif os.path.exists(data_path):
            logging.debug("Copying temporary %s to %s", data_path, temp_data_path)
            shutil.copy(data_path, temp_data_path)
        elif os.path.exists(data_path + ".gz"):
            logging.debug("Gunzipping temporary %s to %s", data_path + ".gz", temp_data_path)
            with open(temp_data_path, "wb") as uncompressed, gzip.open(data_path + ".gz", "rb") as compressed:
                shutil.copyfileobj(compressed, uncompressed)
        elif os.path.exists(data_path + ".fz"):
            logging.debug("Funpacking temporary %s to %s", data_path + ".fz", temp_data_path)
            subprocess.run([FUNPACK_CMD, '-C', '-O', temp_data_path, data_path + ".fz"])
        else:
            logging.error("could not find data file: %s", temp_data_path)
            raise Exception("could not find data file: " + temp_data_path)
            
    return temp_label_path




def run_validator(file_name, schema_path, skip_data):
    '''
    Runs the label validatior on the given file or directory
    '''

    logging.info("Running the validator...")
    params = [VALIDATE_CMD, '-s', 'json', '-E', '1000'] + (['-D'] if skip_data else []) + ['-x', *get_schemas(schema_path, ".xsd"), '-S', *get_schemas(schema_path, ".sch"), '-t', file_name]
    process = subprocess.run(params, stdout=subprocess.PIPE, encoding="utf-8")

    logging.info("Validation complete, processing results...")

    output = re.sub('\}\.+', '}', process.stdout)
    output = re.sub('\.+\{', '{', output)
    
    try:
        result = json.loads(output)
    except JSONDecodeError:
        logging.error(output)
        print(output)
        raise

    failures = [x for x in result['productLevelValidationResults']
                         if x['status'] == "FAIL"]
    successes = [x for x in result['productLevelValidationResults']
                          if x['status'] == "PASS"]

    if failures:
        logging.info("%s Failures encountered", len(failures))
        #logging.error(failure)
        #logging.error(result)
    else:
        logging.info("Validation passed")
    return (failures, successes, output)

def get_schemas(base_path, extension):
    return [os.path.join(base_path, x + extension) for x in DICTIONARIES]
    

class Validation:
    '''
    Runs the validation on a label or directory, and stores the successes
    and failures
    '''
    def __init__(self, dirname):
        result = run_validator(dirname, True)
        self.failures, self.successes = result
