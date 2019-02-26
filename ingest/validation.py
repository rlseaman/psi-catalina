import subprocess
import os.path
import json

MODEL_VERSION='1A00'
SCHEMA_PATH='../schemas' 

IMAGING_SCHEMA=os.path.join(SCHEMA_PATH, 'PDS4_IMG_1A10.xsd')
DISP_SCHEMA=os.path.join(SCHEMA_PATH, 'PDS4_DISP_1B00.xsd')
GEOM_SCHEMA=os.path.join(SCHEMA_PATH, 'PDS4_GEOM_1A10.xsd')
CATALINA_SCHEMA=os.path.join(SCHEMA_PATH, 'pds4_catalina.ldd_CSS_1000.xsd')

IMAGING_SCHEMATRON=os.path.join(SCHEMA_PATH, 'PDS4_IMG_1A10.sch')
DISP_SCHEMATRON=os.path.join(SCHEMA_PATH, 'PDS4_DISP_1B00.sch')
GEOM_SCHEMATRON=os.path.join(SCHEMA_PATH, 'PDS4_GEOM_1A10.sch')
CATALINA_SCHEMATRON=os.path.join(SCHEMA_PATH, 'pds4_catalina.ldd_CSS_1000.sch')


def run_validator(file_name):
    p = subprocess.run(['validate', 
        '-D', 
        '-s', 'json',
        '-m', MODEL_VERSION,
        '-x', IMAGING_SCHEMA, DISP_SCHEMA, GEOM_SCHEMA, CATALINA_SCHEMA,
        '-S', IMAGING_SCHEMATRON, DISP_SCHEMATRON, GEOM_SCHEMATRON, CATALINA_SCHEMATRON,
        '-t', file_name], stdout=subprocess.PIPE)
    stdout = p.stdout
    return json.loads(stdout)

class Validation:
    def __init__(self, dirname):
        result = run_validator(dirname)
        self.failures =  [x for x in result['productLevelValidationResults'] if x['status'] == "FAIL"]
        self.successes =  [x for x in result['productLevelValidationResults'] if x['status'] == "PASS"]
