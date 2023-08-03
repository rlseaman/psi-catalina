#! /usr/bin/env python3

import sys
import os
import os.path
import itertools
import argparse

import json
import cssextract

COLLECTIONS = ['data_calibrated', 'data_derived', 'data_partially_processed', 'data_raw', 'data_reduced']


def main():
    parser = argparse.ArgumentParser(description='Convert the nightly files from the CSS archive into json format')
    parser.add_argument('--basedir', help='The base directory for the delivered data', required=True)
    parser.add_argument('--inst', help='The instrument code for the batch', required=True)
    parser.add_argument('--year', help='The year that the data was delivered', required=True)
    parser.add_argument('--night', help='The observaton night for the data', required=True)
    parser.add_argument('--outfilename', help='The destination file for the JSON output', required=True)
    args = parser.parse_args()

    extracted = extract_night(args.basedir, args.inst, args.year, args.night)

    with open(args.outfilename, 'w') as f:
        json.dump(extracted, f)


def extract_night(directory_name, inst, year, night):
    """
    Extract information from the files in a single directory (which should correspond to
    a combination of instrument and observing night), and return it as a single dictionary.
    """
    print(directory_name)

    files_for_night = get_files_for_night(directory_name, inst, year, night)

    return extract_files(pointing_file=filter_files(files_for_night, has_extension(".point")),
                         coverage_file=filter_files(files_for_night, has_extension(".cov")),
                         control_file=filter_files(files_for_night, has_name("controlconfig.json")),
                         followup_file=filter_files(files_for_night, has_name("followup.txt")),
                         fields_file=filter_files(files_for_night, has_name("userfields.txt")),
                         surveyplan_file=filter_files(directory_name, has_prefix("survey")),
                         astrometry_file=filter_files(files_for_night, has_extension(".mpcd.mrpt")),
                         neo_file=filter_files(files_for_night, has_extension(".neos.mrpt")))


def extract_files(pointing_file, coverage_file, control_file, followup_file, fields_file, surveyplan_file,
                  astrometry_file, neo_file):
    return {
        "pointing": cssextract.process_pointing_file(pointing_file),
        "coverage": cssextract.process_coverage_file(coverage_file),
        "control": cssextract.process_control_file(control_file),
        "followup": cssextract.process_field_file(followup_file),
        "fields": cssextract.process_field_file(fields_file),
        "surveyplan": cssextract.process_plan_file(surveyplan_file) if surveyplan_file else [],
        "neos": cssextract.process_astrometry_file(astrometry_file) if astrometry_file else [],
        "astrometry": cssextract.process_astrometry_file(neo_file) if neo_file else []
    }


def has_extension(extension):
    return lambda x: x.endswith(extension)


def has_prefix(prefix):
    return lambda x: os.path.basename(x).startswith(prefix)


def has_name(name):
    return lambda x: os.path.basename(x) == name


def filter_files(filelist, file_filter):
    candidates = [x for x in filelist if file_filter(x)]
    if candidates:
        return candidates[0]
    return None


def get_files_for_night(search_dir, inst, year, night):
    return list(itertools.chain.from_iterable(
        get_files_in_path(path) for path in get_directories_for_night(search_dir, inst, year, night))
    )


def get_files_in_path(path):
    return (os.path.join(path, filename) for filename in os.listdir(path))


def get_directories_for_night(search_dir, inst, year, night):
    return (os.path.join(search_dir, collection, inst, year, night) for collection in COLLECTIONS)


if __name__ == '__main__':
    sys.exit(main())
