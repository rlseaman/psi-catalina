#! /usr/bin/env python3

import sys
import os
import os.path
import json
import sqlite3
import re

import cssdb

COV_KEYWORDS=['Source:', 'Date:', 'Limiting Magnitude:']
POINT_KEYWORDS=['Observer:']
ASTR_HEADERS = ['COD','OBS','TEL','NET','AC2','MEA','ACK']



def main(argv=None):
    if argv is None:
        argv = sys.argv

    directory_name = argv[1]
    
    extracted = extract_directory(directory_name)
    cssdb.write_directory(extracted, directory_name)

def extract_directory(directory_name):
    '''
    Extract information from the files in a single directory (which should correspond to
    a combination of instrument and observing night), and return it as a single dictionary.
    '''
    print(directory_name)
    pointing_file = get_file_with_extension(directory_name, ".point")
    pointing = process_pointing_file(directory_name, pointing_file)

    coverage_file = get_file_with_extension(directory_name, ".cov")
    coverage = process_coverage_file(directory_name, coverage_file)

    control = process_control_file(directory_name, "controlconfig.json")

    followup = process_field_file(directory_name, "followup.txt")
    fields = process_field_file(directory_name, "userfields.txt")

    surveyplan_file = get_file_with_prefix(directory_name, "survey")

    surveyplan = process_plan_file(directory_name, surveyplan_file) if surveyplan_file else []

    astrometry_file = get_file_with_extension(directory_name, ".mpcd.mrpt")
    astrometry = process_astrometry_file(directory_name, astrometry_file)  if astrometry_file else []

    neo_file = get_file_with_extension(directory_name, ".neos.mrpt")
    neos = process_astrometry_file(directory_name, neo_file)  if neo_file else []

    return {
        "pointing": pointing,
        "coverage": coverage,
        "control": control,
        "followup": followup,
        "fields": fields,
        "surveyplan": surveyplan,
        "neos": neos,
        "astrometry": astrometry
    }


def process_pointing_file(directory_name, pointing_file_name):
    '''
    Convert the contents of the pointing file to a dictionary
    '''
    lines = get_lines(directory_name, pointing_file_name)
    
    obslines = [x for x in lines if '|' in x]
    obsfiles = [x.split("|")[0].strip() for x in obslines]

    keywords = extract_keywords(lines, POINT_KEYWORDS, ":")
    keywords["Observations"] = obsfiles
    return keywords
    

def process_coverage_file(directory_name, coverage_file_name):
    '''
    Convert the contents of the coverage file to a dictionary
    '''
    lines = get_lines(directory_name, coverage_file_name)
    keywords = extract_keywords(lines, COV_KEYWORDS, ":")
    return keywords

def process_control_file(directory_name, control_file_name):
    '''
    Convert the contents of the control file to a dictionary
    '''
    with open(os.path.join(directory_name, control_file_name)) as infile:
        contents = json.load(infile)
    return {
        "Detector": contents["fits"]["detector"],
        "Telescope": contents["fits"]["telescope"]
    }

def process_field_file(directory_name, field_file_name):
    '''
    Convert the contents of the fields file to a list of fields.
    '''
    lines = get_lines(directory_name, field_file_name)
    field_lines = [x for x in lines if not x.startswith("#")]
    fields = [to_field(x) for x in field_lines]
    return fields

    
def to_field(line):
    '''
    Convert a line from the fields file to a dictionary
    '''
    meta = line[37:].strip()
    keywords = dict([[y.strip() for y in x.split('=')] for x in meta.split(";") if x])
    keywords["id"] = line[0:11].strip()
    keywords["ra"] = line[11:24].strip()
    keywords["dec"] = line[24:37].strip()

    if "COM" in keywords:
        comment = keywords["COM"]
        if "Field" in comment:
            field = re.search("Field ([^ ]*)", comment).group(1)
            keywords["field"] = field
    

    return (keywords)

def process_plan_file(directory_name, plan_file_name):
    '''
    Convert the observing plan file to a list of plan items.
    '''
    lines = get_lines(directory_name, plan_file_name)
    plan_lines = [x for x in lines if not x.startswith("#")]
    return [to_plan(x) for x in plan_lines]

def to_plan(line):
    '''
    Convert a line from the observing plan file into a dictionary
    '''
    tokens = line.split()
    return {
        "surveyfield_code": tokens[0],
        "mjd": tokens[1],
        "ra": tokens[2],
        "dec": tokens[3]
    }

def process_astrometry_file(directory_name, file_name):
    '''
    Convert the astrometry file into a list of astrometry items.
    '''
    lines = get_lines(directory_name, file_name)
    astr_lines = [x for x in lines if not any([x.startswith(h) for h in ASTR_HEADERS])]
    return [to_astrometry(x) for x in astr_lines]

def to_astrometry(line):
    '''
    Convert an astrometry line into a dictionary.
    '''
    return {
        "code": line[:12].strip(),
        "date": line[14:32].strip(),
        "ra": line[32:43].strip(),
        "dec": line[44:56].strip(),
        "mag": line[65:69].strip()
    }

def get_lines(directory_name, file_name):
    '''
    Extract all of the lines from a file.
    '''
    filepath = os.path.join(directory_name, file_name)
    if os.path.exists(filepath):
        with open(filepath) as infile:
            return infile.readlines()
    
    return []


def get_file_with_extension(directory_name, extension):
    '''
    Locates the first file in a directory with a given extension.
    '''
    candidates = [x for x in os.listdir(directory_name) if x.endswith(extension)]
    if candidates:
        return candidates[0]
    return None

def get_file_with_prefix(directory_name, prefix):
    '''
    Locates the first file in a directory with a given prefix.
    '''
    candidates = [x for x in os.listdir(directory_name) if x.startswith(prefix)]
    if candidates:
        return candidates[0]
    return None


def extract_keywords(lines, keywords, delimiter):
    '''
    Treates a list of lines as a list of delimited name-value pairs.
    Finds all of the name-value pairs that match the provied list, and converts them into a dictionary.
    '''
    keyword_lines = [l for l in lines if any([k in l for k in keywords])]
    keyword_pairs = [[v.strip() for v in l.split(delimiter)] for l in keyword_lines]
    return dict(keyword_pairs)


if __name__ == '__main__':
    sys.exit(main())
