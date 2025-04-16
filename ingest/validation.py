"""
Performs validation on a PDS4 label
"""
from json.decoder import JSONDecodeError
import subprocess
import os.path
import os
import json
import product
import tempfile
import shutil
import gzip
import logging
import re

from product import ObsNight

VALIDATE_CMD = 'validate'
FUNPACK_CMD = 'funpack'


class ValidationResult:
    def __init__(self, vresult: dict) -> None:
        self.status = vresult.get("status", "")
        self.labelpath = vresult.get("label", "")
        self.messages = [ValidationMessage(x) for x in vresult.get("messages")]
        self.dataContents = [ValidationData(x) for x in vresult.get("dataContents")]
        self.src = vresult


class ValidationMessage:
    def __init__(self, vmessage: dict) -> None:
        self.severity = vmessage.get("severity", "")
        self.type = vmessage.get("type", "")
        self.line = vmessage.get("line")
        self.column = vmessage.get("column")
        self.message = vmessage.get("message")


class ValidationData:
    def __init__(self, vdata: dict) -> None:
        self.datafile = vdata.get("dataFile")
        self.messages = [ValidationMessage(x) for x in vdata.get("messages")]


def validate_product(candidate: product.Product,
                     schema_path: str,
                     skip_data: bool) -> tuple[list[ValidationResult], list[ValidationResult], str]:
    """
    Moves the entirety of the product to a temporary location,
    decompressed the data files if needed, and validates the product.
    """
    return validate_products([candidate], schema_path, skip_data)


def validate_products(products: list[product.Product],
                      schema_path: str,
                      skip_data: bool) -> tuple[list[ValidationResult], list[ValidationResult], str]:
    """
    Moves the entirety of the product to a temporary location,
    decompressed the data files if needed, and validates the product.
    """
    with tempfile.TemporaryDirectory() as temp:
        logging.info(f"Validating products at: {temp}")
        temp_dir = temp
        for product_to_copy in products:
            create_temp_copy(temp_dir, product_to_copy, skip_data)

        return run_validator(temp_dir, schema_path, skip_data)


def create_temp_copy(temp_dir: str, product_to_copy: product.Product, skip_data: bool) -> str:
    """
    Creates temporary copies of the files for a product. Temporary copies are
    needed because the real copies are compressed, and the labels also need
    to be copied so that they can be modified to point to these copies.

    The labels are not changed in place because they should not be changed
    until they are validated.

    If data validation is being skipped, this will still create an empty
    dummy file, so that the validator will not fail.
    """
    label_file_name = product_to_copy.labelfilename
    label_path = product_to_copy.labelpath
    data_dir = product_to_copy.datadir

    temp_product_dir = os.path.join(temp_dir,
                                    product_to_copy.night.inst,
                                    product_to_copy.night.year,
                                    product_to_copy.night.date)

    logging.info(f"Creating temporary copies of {label_file_name}")

    os.makedirs(temp_product_dir, exist_ok=True)

    temp_label_path = os.path.join(temp_product_dir, label_file_name)
    shutil.copy(label_path, temp_label_path)

    data_file_names = product_to_copy.filenames()
    for data_file_name in data_file_names:
        data_path = os.path.join(data_dir, data_file_name)
        temp_data_path = os.path.join(temp_product_dir, data_file_name)

        if skip_data:
            logging.debug(f"Creating dummy copy of {data_path}")
            with open(temp_data_path, "w") as _:
                pass
        elif os.path.exists(data_path):
            logging.debug(f"Copying temporary {data_path} to {temp_data_path}")
            shutil.copy(data_path, temp_data_path)
        elif os.path.exists(f"{data_path}.gz"):
            logging.debug(f"Gunzipping temporary {data_path}.gz to {temp_data_path}")
            try:
                with open(temp_data_path, "wb") as uncompressed, gzip.open(f"{data_path}.gz", "rb") as compressed:
                    shutil.copyfileobj(compressed, uncompressed)
            except (IOError, OSError):
                logging.warning(f"Could not decompress {data_path}.gz to {temp_data_path}")
        elif os.path.exists(f"{data_path}.fz"):
            logging.debug(f"Funpacking temporary {data_path} to {temp_data_path}")
            subprocess.run([FUNPACK_CMD, '-C', '-O', temp_data_path, f"{data_path}.fz"])
        else:
            logging.error(f"could not find data file: {temp_data_path}")

    return temp_label_path


def run_validator(file_name: str,
                  schema_path: str,
                  skip_data: bool) -> tuple[list[ValidationResult], list[ValidationResult], str]:
    """
    Runs the label validatior on the given file or directory
    """

    logging.info("Running the validator...")
    params = [VALIDATE_CMD, '-s', 'json', '-E', '2147483647'] + (['-D'] if skip_data else []) + \
             ['-C', os.path.join(schema_path, 'catalog_all.xml'), '-t', file_name]
    process = subprocess.run(params, stdout=subprocess.PIPE, encoding="utf-8")

    logging.info("Validation complete, processing results...")

    unfiltered = process.stdout

    output = re.sub(r'}\.+', '}', unfiltered)
    output = re.sub(r'\.+\{', '{', output)
    output = re.sub(r'}Completed execution in.+', '}',  output)

    try:
        result = json.loads(output)
    except JSONDecodeError:
        logging.error(output)
        print(output)
        raise

    failures = [ValidationResult(x) for x in result['productLevelValidationResults']
                if x['status'] == "FAIL"]
    successes = [ValidationResult(x) for x in result['productLevelValidationResults']
                 if x['status'] == "PASS"]

    if failures:
        filenames = [os.path.basename(x.labelpath) for x in failures]
        logging.warning(f"{len(failures)} Failures encountered: {','.join(filenames)}")
    else:
        logging.info("Validation passed")
    return failures, successes, unfiltered


def extract_label_info(labelpath: str) -> tuple[ObsNight, str]:
    datepath = os.path.dirname(labelpath)
    yearpath = os.path.dirname(datepath)
    instpath = os.path.dirname(yearpath)

    label = os.path.basename(labelpath)
    dateval = os.path.basename(datepath)
    yearval = os.path.basename(yearpath)
    instval = os.path.basename(instpath)

    return ObsNight(instval, yearval, dateval), label


