#! /usr/bin/env python3

import sys
import os
import os.path
import itertools
import argparse
import datetime

import json
import cssextract


COLLECTIONS=['data_calibrated', 'data_derived', 'data_partially_processed', 'data_raw', 'data_reduced']
INSTS = ['703', 'G96', 'I52', 'V06']
def main(argv=None):

    parser = argparse.ArgumentParser(description='Convert the nightly files from the CSS archive into json format')
    parser.add_argument('--basedir', help='The base directory for the delivered data', required=True)
    parser.add_argument('--nights', help='Number of nights to look back', required=True, type=int)
    parser.add_argument('--outfilebase', help='The base file for the JSON output', required=True)
    args = parser.parse_args()

    dates = [datetime.date.today() - datetime.timedelta(x) for x in range(0, args.nights)]

    for inst in INSTS:
        for d in dates:
            night = d.strftime("%y%b%d")
            year = d.strftime("%Y")

            outfilename = args.outfilebase + night + ".json"

            if not os.path.exists(outfilename):
                extracted = extract_night(args.basedir, inst, year, night)
                print (extracted)
        
                if extracted:
                    with open(outfilename, 'w') as f:
                        json.dump(extracted, f)
            else:
                print("Output file exists: %s, skipping..." % outfilename)

def extract_night(directory_name, inst, year, night):
    '''
    Extract information from the files in a single directory (which should correspond to
    a combination of instrument and observing night), and return it as a single dictionary.
    '''

    files_for_night=get_files_for_night(directory_name, inst, year, night)

    if files_for_night:
        return extract_files(pointing_file=first_matching_file(files_for_night, has_extension(".point")),
                            coverage_file=first_matching_file(files_for_night, has_extension(".cov")), 
                            control_file=first_matching_file(files_for_night, has_name("controlconfig.json")), 
                            followup_file=first_matching_file(files_for_night, has_name("followup.txt")), 
                            fields_file=first_matching_file(files_for_night, has_name("userfields.txt")), 
                            surveyplan_file=first_matching_file(directory_name, has_prefix("survey")), 
                            astrometry_file=first_matching_file(files_for_night, has_extension(".mpcd.mrpt")), 
                            neo_file=first_matching_file(files_for_night, has_extension(".neos.mrpt")))
    else:
        print ("No data for %s, %s, %s" % (inst, year, night))

def extract_files(pointing_file, coverage_file, control_file, followup_file, fields_file, surveyplan_file, astrometry_file, neo_file):
    return {
        "pointing": cssextract.process_pointing_file(pointing_file),
        "coverage": cssextract.process_coverage_file(coverage_file) if coverage_file else [],
        "control": cssextract.process_control_file(control_file),
        "followup": cssextract.process_field_file(followup_file) if followup_file else [],
        "fields": cssextract.process_field_file(fields_file) if fields_file else [],
        "surveyplan": cssextract.process_plan_file(surveyplan_file) if surveyplan_file else [],
        "neos": cssextract.process_astrometry_file(astrometry_file)  if astrometry_file else [],
        "astrometry": cssextract.process_astrometry_file(neo_file)  if neo_file else []
    }

def has_extension(extension):
    return lambda x: x.endswith(extension)

def has_prefix(prefix):
    return lambda x: os.path.basename(x).startswith(prefix)

def has_name(name):
    return lambda x: os.path.basename(x) == name

def first_matching_file(filelist, filter):
    candidates = [x for x in filelist if filter(x)]
    if candidates:
        return candidates[0]
    return None

def get_files_for_night(search_dir, inst, year, night):
    directories = get_directories_for_night(search_dir, inst, year, night)
    if directories:
        return list(itertools.chain.from_iterable(
            get_files_in_path(path) for path in directories)
        )

def get_files_in_path(path):
    return (os.path.join(path, filename) for filename in os.listdir(path))

def get_directories_for_night(search_dir, inst="", year="", night=""):
    candidates = (os.path.join(search_dir, collection, inst, year, night) for collection in COLLECTIONS)
    return [x for x in candidates if os.path.exists(x)]

if __name__ == '__main__':
    sys.exit(main())
