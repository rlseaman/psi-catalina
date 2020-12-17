#! /usr/bin/env python3

import sys
import os
import os.path
import cssextract

import cssdb

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
    pointing = cssextract.process_pointing_file(directory_name, pointing_file)

    coverage_file = get_file_with_extension(directory_name, ".cov")
    coverage = cssextract.process_coverage_file(directory_name, coverage_file)

    control = cssextract.process_control_file(directory_name, "controlconfig.json")

    followup = cssextract.process_field_file(directory_name, "followup.txt")
    fields = cssextract.process_field_file(directory_name, "userfields.txt")

    surveyplan_file = get_file_with_prefix(directory_name, "survey")

    surveyplan = cssextract.process_plan_file(directory_name, surveyplan_file) if surveyplan_file else []

    astrometry_file = get_file_with_extension(directory_name, ".mpcd.mrpt")
    astrometry = cssextract.process_astrometry_file(directory_name, astrometry_file)  if astrometry_file else []

    neo_file = get_file_with_extension(directory_name, ".neos.mrpt")
    neos = cssextract.process_astrometry_file(directory_name, neo_file)  if neo_file else []

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


if __name__ == '__main__':
    sys.exit(main())
