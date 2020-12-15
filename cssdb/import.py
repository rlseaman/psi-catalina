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
    write_directory(extracted, directory_name)

def extract_directory(directory_name):
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
    lines = get_lines(directory_name, pointing_file_name)
    
    obslines = [x for x in lines if '|' in x]
    obsfiles = [x.split("|")[0].strip() for x in obslines]

    keywords = extract_keywords(lines, POINT_KEYWORDS, ":")
    keywords["Observations"] = obsfiles
    return keywords
    

def process_coverage_file(directory_name, coverage_file_name):
    lines = get_lines(directory_name, coverage_file_name)
    keywords = extract_keywords(lines, COV_KEYWORDS, ":")
    return keywords

def process_control_file(directory_name, control_file_name):
    with open(os.path.join(directory_name, control_file_name)) as infile:
        contents = json.load(infile)
    return {
        "Detector": contents["fits"]["detector"],
        "Telescope": contents["fits"]["telescope"]
    }

def process_field_file(directory_name, field_file_name):
    lines = get_lines(directory_name, field_file_name)
    field_lines = [x for x in lines if not x.startswith("#")]
    fields = [to_field(x) for x in field_lines]
    return fields

    
def to_field(line):
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
    lines = get_lines(directory_name, plan_file_name)
    plan_lines = [x for x in lines if not x.startswith("#")]
    return [to_plan(x) for x in plan_lines]

def to_plan(line):
    tokens = line.split()
    return {
        "surveyfield_code": tokens[0],
        "mjd": tokens[1],
        "ra": tokens[2],
        "dec": tokens[3]
    }

def process_astrometry_file(directory_name, file_name):
    lines = get_lines(directory_name, file_name)
    astr_lines = [x for x in lines if not any([x.startswith(h) for h in ASTR_HEADERS])]
    return [to_astrometry(x) for x in astr_lines]

def to_astrometry(line):
    return {
        "code": line[:12].strip(),
        "date": line[14:32].strip(),
        "ra": line[32:43].strip(),
        "dec": line[44:56].strip(),
        "mag": line[65:69].strip()
    }

def get_lines(directory_name, file_name):
    filepath = os.path.join(directory_name, file_name)
    if os.path.exists(filepath):
        with open(filepath) as infile:
            return infile.readlines()
    
    return []


def get_file_with_extension(directory_name, extension):
    candidates = [x for x in os.listdir(directory_name) if x.endswith(extension)]
    if candidates:
        return candidates[0]
    return None

def get_file_with_prefix(directory_name, prefix):
    candidates = [x for x in os.listdir(directory_name) if x.startswith(prefix)]
    if candidates:
        return candidates[0]
    return None


def extract_keywords(lines, keywords, delimiter):
    keyword_lines = [l for l in lines if any([k in l for k in keywords])]
    keyword_pairs = [[v.strip() for v in l.split(delimiter)] for l in keyword_lines]
    return dict(keyword_pairs)

def write_directory(extracted, directory_name):
    conn = sqlite3.connect("cssdb.sqlite")
    c = conn.cursor()

    night_id = write_obsnight(c, extracted, directory_name)

    for followup in extracted["followup"]:
        write_followup(c, night_id, followup)

    for userfield in extracted["fields"]:
        write_userfield(c, night_id, userfield)

    for observation in extracted["pointing"]["Observations"]:
        write_observation(c, night_id, observation)

    for surveyplan in extracted["surveyplan"]:
        write_plan(c, night_id, surveyplan)

    for astr in extracted["astrometry"]:
        write_astr(c, night_id, astr)

    for neo in extracted["neos"]:
        write_neo(c, night_id, neo)

    conn.commit()
    conn.close()


def write_obsnight(c, extracted, directory_name):
    params = ('CSS',
        extracted['coverage']['Source'],
        extracted['control']['Telescope'],
        extracted['control']['Detector'],
        extracted['coverage']['Date'],
        extracted['pointing']['Observer'],
        extracted['coverage']['Limiting Magnitude'],
        directory_name
    )

    return exec_insert_key(c, cssdb.OBSNIGHT_INSERT, params)

def write_followup(c, night_id, followup):
    params = (
        followup["id"],
        followup.get("NAME", None),
        followup["ra"],
        followup["dec"],
        followup["MAG"],
        followup["COM"],
        followup.get("field", None),
        night_id
    )

    c.execute(cssdb.FOLLOWUP_INSERT, params)

def write_userfield(c, night_id, userfield):
    params = (
        userfield["id"],
        userfield.get("NAME", None),
        userfield["ra"],
        userfield["dec"],
        userfield["MAG"],
        userfield.get("COM", None),
        userfield.get("field", None),
        night_id
    )

    c.execute(cssdb.USERFIELD_INSERT, params)

def write_observation(c, night_id, obsfile):
    params = (night_id, obsfile)
    c.execute(cssdb.OBS_INSERT, params)

def write_plan(c, night_id, plan):
    params = (
        plan["surveyfield_code"],
        plan["mjd"],
        plan["ra"],
        plan["dec"],
        night_id
    )
    c.execute(cssdb.SURVEYFIELD_INSERT, params)

def write_astr(c, night_id, astr):
    params = (
        astr["code"],
        astr["date"],
        astr["ra"],
        astr["dec"],
        astr["mag"],        
        night_id
    )
    c.execute(cssdb.ASTR_INSERT, params)

def write_neo(c, night_id, neo):
    params = (
        neo["code"],
        neo["date"],
        neo["ra"],
        neo["dec"],
        neo["mag"],        
        night_id
    )
    c.execute(cssdb.NEO_INSERT, params)


def exec_insert_key(c, sql, params):
    c.execute(sql, params)
    c.execute("select last_insert_rowid()")
    return c.fetchone()[0]

if __name__ == '__main__':
    sys.exit(main())