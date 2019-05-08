'''
Performs validation on a PDS4 label
'''
import subprocess
import os.path
import json

MODEL_VERSION = '1A00'
SCHEMA_PATH = '../schemas'

DICTIONARIES = ['PDS4_IMG_1A10_1510',
                'PDS4_DISP_1B00',
                'PDS4_GEOM_1A10',
                'pds4_catalina.ldd_CSS_1000']

SCHEMA_FILES = [x + '.xsd' for x in DICTIONARIES]
SCHEMATRON_FILES = [x + '.sch' for x in DICTIONARIES]
SCHEMA_PATHS = [os.path.join(SCHEMA_PATH, x) for x in SCHEMA_FILES]
SCHEMATRON_PATHS = [os.path.join(SCHEMA_PATH, x) for x in SCHEMATRON_FILES]

def run_validator(file_name):
    '''
    Runs the label validatior on the given file or directory
    '''
    process = subprocess.run(['validate',
                              '-D',
                              '-s', 'json',
                              '-m', MODEL_VERSION,
                              '-x', *SCHEMA_PATHS,
                              '-S', *SCHEMATRON_PATHS,
                              '-t', file_name], stdout=subprocess.PIPE)
    stdout = process.stdout
    return json.loads(stdout)

class Validation:
    '''
    Runs the validation on a label or directory, and stores the successes
    and failures
    '''
    def __init__(self, dirname):
        result = run_validator(dirname)
        self.failures = [x for x in result['productLevelValidationResults']
                         if x['status'] == "FAIL"]
        self.successes = [x for x in result['productLevelValidationResults']
                          if x['status'] == "PASS"]
