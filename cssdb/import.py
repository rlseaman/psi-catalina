#! /usr/bin/env python3

import sys
import os
import os.path
import cssextract

import cssdb
import json

def main(argv=None):
    if argv is None:
        argv = sys.argv

    directory_name = argv[1]
    
    extracted = extract_directory(directory_name)
    
    print(json.dumps(extracted))
    cssdb.write_directory(extracted, directory_name)

def extract_directory(directory_name):
    '''
    Extract information from the files in a single directory (which should correspond to
    a combination of instrument and observing night), and return it as a single dictionary.
    '''
    print(directory_name)
    pointing_file = get_file_with_extension(directory_name, ".point")
    coverage_file = get_file_with_extension(directory_name, ".cov")
    control_file = os.path.join(directory_name, "controlconfig.json")
    followup_file = os.path.join(directory_name, "followup.txt")
    fields_file = os.path.join(directory_name, "userfields.txt")
    surveyplan_file = get_file_with_prefix(directory_name, "survey")
    astrometry_file = get_file_with_extension(directory_name, ".mpcd.mrpt")
    neo_file = get_file_with_extension(directory_name, ".neos.mrpt")
    
    return extract_files(pointing_file, 
                        coverage_file, 
                        control_file, 
                        followup_file, 
                        fields_file, 
                        surveyplan_file, 
                        astrometry_file, 
                        neo_file)

def extract_files(pointing_file, coverage_file, control_file, followup_file, fields_file, surveyplan_file, astrometry_file, neo_file):
    pointing = cssextract.process_pointing_file(pointing_file)
    coverage = cssextract.process_coverage_file(coverage_file)
    control = cssextract.process_control_file(control_file)
    followup = cssextract.process_field_file(followup_file)
    fields = cssextract.process_field_file(fields_file)
    surveyplan = cssextract.process_plan_file(surveyplan_file) if surveyplan_file else []
    astrometry = cssextract.process_astrometry_file(astrometry_file)  if astrometry_file else []
    neos = cssextract.process_astrometry_file(neo_file)  if neo_file else []

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
        return os.path.join(directory_name, candidates[0])
    return None

def get_file_with_prefix(directory_name, prefix):
    '''
    Locates the first file in a directory with a given prefix.
    '''
    candidates = [x for x in os.listdir(directory_name) if x.startswith(prefix)]
    if candidates:
        return os.path.join(directory_name, candidates[0])
    return None


if __name__ == '__main__':
    sys.exit(main())
