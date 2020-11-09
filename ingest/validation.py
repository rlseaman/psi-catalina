'''
Performs validation on a PDS4 label
'''
import subprocess
import os.path
import json
import product
import tempfile
import shutil
import gzip
import logging

SCHEMA_PATH = '../schemas'

DICTIONARIES = ['PDS4_IMG_1900',
                'PDS4_DISP_1900',
                'PDS4_GEOM_1900_1510',
                'PDS4_SURVEY_1A00_1000']

SCHEMA_FILES = [x + '.xsd' for x in DICTIONARIES]
SCHEMATRON_FILES = [x + '.sch' for x in DICTIONARIES]
SCHEMA_PATHS = [os.path.join(SCHEMA_PATH, x) for x in SCHEMA_FILES]
SCHEMATRON_PATHS = [os.path.join(SCHEMA_PATH, x) for x in SCHEMATRON_FILES]

VALIDATE_CMD='validate'
FUNPACK_CMD='funpack'

def validate_product(product, skip_data):
    '''
    Moves the entirety of the product to a temporary location,
    decompressed the data files if needed, and validates the product.
    '''
    with tempfile.TemporaryDirectory() as temp:
        temp_dir = temp
        temp_label_path = create_temp_copy(temp_dir, product)
        return run_validator(temp_label_path, skip_data)

def create_temp_copy(temp_dir, product):
    label_file_name = product.labelfilename
    label_path = product.labelpath
    data_dir = product.datadir

    logging.info("Creating temporary copies of %s", label_file_name)

    temp_label_path = os.path.join(temp_dir, label_file_name)
    shutil.copy(label_path, temp_label_path)

    data_file_names = product.file_names()
    for data_file_name in data_file_names:
        data_path = os.path.join(data_dir, data_file_name)
        temp_data_path = os.path.join(temp_dir, data_file_name)

        if os.path.exists(data_path):
            logging.info("Copying temporary %s to %s", data_path, temp_data_path)
            shutil.copy(data_path, temp_data_path)
        elif os.path.exists(data_path + ".gz"):
            logging.info("Gunzipping temporary %s to %s", data_path + ".gz", temp_data_path)
            with open(temp_data_path, "wb") as uncompressed, open(data_path + ".gz", "rb") as compressed:
                shutil.copyfileobj(compressed, uncompressed)
        elif os.path.exists(data_path + ".fz"):
            logging.info("Funpacking temporary %s to %s", data_path + ".fz", temp_data_path)
            subprocess.run([FUNPACK_CMD, '-C', '-O', temp_data_path, data_path + ".fz"])
        else:
            logging.error("could not find data file: %s", temp_data_path)
            raise Exception("could not find data file: " + temp_data_path)
            
    return temp_label_path


def validate_products(products):
    '''
    Moves the entirety of the product to a temporary location,
    decompressed the data files if needed, and validates the product.
    '''
    with tempfile.TemporaryDirectory() as temp:
        logging.info("Validating products at: %s", temp)
        temp_dir = temp
        for product in products:
            create_temp_copy(temp_dir, product)

        return run_validator(temp_dir)


def run_validator(file_name, skip_data):
    '''
    Runs the label validatior on the given file or directory
    '''

    params = [VALIDATE_CMD, '-s', 'json'] + (['-D'] if skip_data else []) + ['-x', *SCHEMA_PATHS, '-S', *SCHEMATRON_PATHS, '-t', file_name]

    process = subprocess.run(params, stdout=subprocess.PIPE)
    stdout = process.stdout
    
    result = json.loads(stdout)
    failures = [x for x in result['productLevelValidationResults']
                         if x['status'] == "FAIL"]
    successes = [x for x in result['productLevelValidationResults']
                          if x['status'] == "PASS"]
    return (failures, successes, stdout)

class Validation:
    '''
    Runs the validation on a label or directory, and stores the successes
    and failures
    '''
    def __init__(self, dirname):
        result = run_validator(dirname)
        self.failures, self.successes = result
