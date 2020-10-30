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

SCHEMA_PATH = '../schemas'

DICTIONARIES = ['PDS4_IMG_1A10_1510',
                'PDS4_DISP_1B00',
                'PDS4_GEOM_1A10',
                'PDS4_SURVEY_1000']

SCHEMA_FILES = [x + '.xsd' for x in DICTIONARIES]
SCHEMATRON_FILES = [x + '.sch' for x in DICTIONARIES]
SCHEMA_PATHS = [os.path.join(SCHEMA_PATH, x) for x in SCHEMA_FILES]
SCHEMATRON_PATHS = [os.path.join(SCHEMA_PATH, x) for x in SCHEMATRON_FILES]

VALIDATE_CMD='validate'

def validate_product(label_path, data_dir):
    '''
    Moves the entirety of the product to a temporary location,
    decompressed the data files if needed, and validates the product.
    '''
    with tempfile.TemporaryDirectory() as temp:
        temp_dir = temp.name

        label_file_name = os.path.basename(label_path)
        temp_label_path = os.path.join(temp_dir, label_file_name)
        shutil.copy(label_path, temp_label_path)
        p = product.Product(temp_label_path)
        data_file_names = p.keywords['file_names']
        for data_file_name in data_file_names:
            data_path = os.path.join(data_dir, data_file_name)
            temp_data_path = os.path.join(data_dir, data_file_name)

            if data_file_name.endswith(".gz"):
                temp_data_path = temp_data_path.replace(".gz", "")
                with open(temp_data_path, "wb") as uncompressed, open(data_path, "rb") as compressed:
                    shutil.copyfileobj(compressed, uncompressed)
            else:
                shutil.copy(data_path, temp_data_path)

        return run_validator(temp_label_path)

def run_validator(file_name):
    '''
    Runs the label validatior on the given file or directory
    '''
    process = subprocess.run([VALIDATE_CMD,
                              '-s', 'json',
                              '-x', *SCHEMA_PATHS,
                              '-S', *SCHEMATRON_PATHS,
                              '-t', file_name], stdout=subprocess.PIPE)
    stdout = process.stdout
    
    result = json.loads(stdout)
    failures = [x for x in result['productLevelValidationResults']
                         if x['status'] == "FAIL"]
    successes = [x for x in result['productLevelValidationResults']
                          if x['status'] == "PASS"]
    return (failures, successes)

class Validation:
    '''
    Runs the validation on a label or directory, and stores the successes
    and failures
    '''
    def __init__(self, dirname):
        result = run_validator(dirname)
        self.failures, self.successes = result
