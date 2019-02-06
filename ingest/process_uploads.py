#! /usr/bin/env python3
'''
Python script to process submissions from Catalina Sky Survey and convert them
to PDS4 format.
'''

import sys

import os
import os.path
import itertools
from bs4 import BeautifulSoup

INSTRUMENTS = ['G96']
IGNORE_FILES = ['signature.md5', '.autoxfer']
IGNORE_DATES = ['pds4']
DEST_BASE = '.'

def main(argv=None):
    '''
    Extract command line arguments, ensure that the script is not already running,
    and process the current upload directory.
    '''
    if argv is None:
        argv = sys.argv

    basedir = argv[1]

    lockfile = os.path.join(basedir, ".lockfile")
    if not os.path.exists(lockfile):
        with open(lockfile, "w") as lock:
            lock.write(".")
        try:
            process_upload_dir(basedir)
        finally:
            os.remove(lockfile)

    return 0

def process_upload_dir(basedir):
    '''
    Process the given submission directory.

    The format of a submission directory is inst/year/date,
    so we will process each instrument first.
    '''
    lidvids = []
    for instrument in INSTRUMENTS:
        lidvids.extend(process_inst_directory(basedir, instrument))

    collection_lids = index(lidvids, extract_collection_id)

    for collection_id in collection_lids:
        process_collection(collection_lids, collection_id)

def process_collection(collection_lids, collection_id):
    '''
    Create the collection inventory and label.
    '''
    collection_lidvids = collection_lids[collection_id]
    collection_path = os.path.join(DEST_BASE, collection_id)
    os.makedirs(collection_path, exist_ok=True)
    major, minor = get_last_version_number(collection_path)
    inventory = read_inventory(major, minor, collection_id, collection_path)
    inventory.extend(['P,' + x for x in collection_lidvids])
    newmajor = major + 1
    newminor = 0
    write_inventory(newmajor, newminor, inventory, collection_id, collection_path)

    template_filename = "collection_template.xml"
    write_collection(newmajor, newminor, template_filename, collection_id, collection_path)

def get_last_version_number(collection_path):
    '''
    Gets the most recent known version number for a collection
    '''
    collection_files = [x for x in os.scandir(collection_path) if is_collection_file(x)]
    if collection_files:
        collection_labels = [parselabel(x) for x in collection_files]
        collection_versions = [extract_version(x) for x in collection_labels]
        return max(collection_versions)
    return (0, 0)

def is_collection_file(candidate):
    '''
    Determine if the passed in file is a collection file.
    '''
    return candidate.name.startswith('collection') and candidate.name.endswith('.xml')

def read_inventory(major, minor, collection_id, collection_dir):
    '''
    Reads in the inventory for the most recent collection update before this one
    '''
    if major:
        collection_filename = 'collection_%s_%s.%s.csv' % (collection_id, major, minor)
        collection_path = os.path.join(collection_dir, collection_filename)
        return open(collection_path).readlines()
    return []

def write_inventory(major, minor, inventory, collection_id, collection_dir):
    '''
    Writes the collection inventory to a file
    '''
    collection_filename = 'collection_%s_%s.%s.csv' % (collection_id, major, minor)
    collection_path = os.path.join(collection_dir, collection_filename)
    write_file(collection_path, '\r\n'.join(inventory) + '\r\n')

def write_collection(major, minor, template_filename, collection_id, collection_dir):
    '''
    Writes the collection label to a file.
    '''
    template = read_file(template_filename)
    contents = template % (collection_id, major, minor)
    collection_filename = 'collection_%s_%s.%s.xml' % (collection_id, major, minor)
    collection_path = os.path.join(collection_dir, collection_filename)
    write_file(collection_path, contents)

def process_inst_directory(basedir, instrument):
    '''
    Processes the given instrument directory

    Inside of an instrument directory, the labels are organized in subdirectories by year.
    '''
    instdir = os.path.join(basedir, instrument)

    years = [x.name for x in os.scandir(instdir) if x.is_dir()]

    result = []
    for year in years:
        yeardir = os.path.join(instdir, year)
        result.extend(process_year_directory(yeardir, instrument, year))
    return result

def process_year_directory(yeardir, instrument, year):
    '''
    Processes the given year directory.

    Inside of a year directory, the labels are organized in subdirectories by date.
    '''
    dates = [x.name for x in os.scandir(yeardir) if x.is_dir() and x.name not in IGNORE_DATES]
    result = []
    for date in dates:
        datadir = os.path.join(yeardir, date)
        labeldir = os.path.join(yeardir, "pds4", date)
        result.extend(process_data(datadir, labeldir, instrument, year, date))
    return result



def process_data(datadir, labeldir, instrument, year, date):
    '''
    Processes the data in a given data directory and label directory pair.

    This checks for a semaphore file before actually doing the processing.
    '''
    if semaphore_exists(datadir) and semaphore_exists(labeldir):
        return process_uploads(datadir, labeldir, instrument, year, date)
    return []
    #update_archive(archive_dir, changes)

def update_archive(archive_dir, changes):
    '''
    Placeholder for code to actually upload data to the archive site
    '''

def semaphore_exists(dirname):
    '''
    Verifies that a semaphore file exists in the given directory.
    '''
    semaphore_file = os.path.join(dirname, '.autoxfer')
    return os.path.exists(semaphore_file)

def process_uploads(datadir, labeldir, instrument, year, date):
    '''
    Processes the data in a given data directory and label directory pair.
    '''
    files = [os.path.join(labeldir, x.name) for x in os.scandir(labeldir) if is_label(x)]
    labels = parselabels(files)

    # move the files to the archive directory
    for label in labels:
        collection_id = label['collection_id']
        dest_directory = os.path.join(DEST_BASE, collection_id, instrument, year, date)
        os.makedirs(dest_directory, exist_ok=True)

        src_data = os.path.join(datadir, label['file_name'])
        dest_data = os.path.join(dest_directory, label['file_name'])
        os.rename(src_data, dest_data)

        src_label = os.path.join(labeldir, label['label_file_name'])
        dest_label = os.path.join(dest_directory, label['label_file_name'])
        os.rename(src_label, dest_label)

    lids = [(l['collection_id'], l['logical_id']) for l in labels]

    collection_products = {}
    for collection_id, logical_id in lids:
        collection_products.setdefault(collection_id, []).append(logical_id)

    lidvids = [l['logical_id'] + "::" + l['version_id'] for l in labels]

    return lidvids

def is_label(candidate):
    '''
    Determines if the given file is a label file.
    '''
    return candidate.name.endswith('.xml')


def parselabels(files):
    '''
    Extracts the keywords from a list of label files.
    '''
    # find all .xml files
    xmlfiles = [x for x in files if x.endswith('.xml')]
    return [extractlabel(parselabel(x), x) for x in xmlfiles]

def find_files(dirname):
    '''
    Gets all of the files in a directory.
    '''
    filelists = [[os.path.join(subdir, f) for f in files] for subdir, _, files in os.walk(dirname)]
    return itertools.chain.from_iterable(filelists)

def extractlabel(label, labelfilename):
    '''
    Extracts keywords from a label file.
    '''
    product_element = label.Product_Observational
    if product_element:
        result = {}
        result['label_file_name'] = os.path.basename(labelfilename)

        idenfication_area = product_element.Identification_Area
        lid = idenfication_area.logical_identifier.string
        result['logical_id'] = lid
        result['collection_id'] = extract_collection_id(lid)
        result['version_id'] = idenfication_area.version_id.string

        file_area = product_element.File_Area_Observational
        result['file_name'] = os.path.basename(file_area.File.file_name.string)
        return result

    return None


def extract_version(label):
    '''
    Extracts the version number from a collection label.
    '''
    product_element = label.Product_Collection
    if product_element:
        identification_area = product_element.Identification_Area
        version = identification_area.version_id.string
        return [int(x) for x in version.split(".")]

    return (0, 0)

def parselabel(filename):
    '''
    Parses a label file into an xml document.
    '''
    with open(filename) as infile:
        return BeautifulSoup(infile, 'lxml-xml')

def ignore(file):
    '''
    Determines if a file should be ignored when processing.
    '''
    return any((file.endswith(name) for name in IGNORE_FILES))

def extract_collection_id(lid):
    '''
    Extracts the collection id component from a LID
    '''
    return lid.split(':')[4]

def index(items, indexfunc):
    '''
    Indexes a list of objects based on the output of a supplied function
    '''
    dictionary = {}
    for item in items:
        key = indexfunc(item)
        dictionary.setdefault(key, []).append(item)
    return dictionary

def read_file(filename):
    '''
    One-liner to read a file
    '''
    with open(filename) as infile:
        return infile.read()

def write_file(filename, contents):
    '''
    One-liner to write a file
    '''
    path = os.path.dirname(filename)
    os.makedirs(path, exist_ok=True)
    with open(filename, "w") as outfile:
        outfile.write(contents)


if __name__ == '__main__':
    sys.exit(main())
