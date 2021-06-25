import sqlite3
import logging
import hashlib

def make_insert_template(tablename, fields):
    return "INSERT INTO {}({}) VALUES ({})".format(
        tablename,
        ",".join(fields),
        ",".join(["?"] * len(fields))
    )

def make_update_templates(tablename, fields, pk_fields):
    assigns = [x + " = ?" for x in fields]
    wheres = [x + " = ?" for x in pk_fields]
    return "UPDATE {} SET {} WHERE {}".format(
        tablename,
        ",".join(assigns),
        " AND ".join(wheres)
    )

def make_search_template(tablename, fields, search_fields):
    wheres = [x + " = ?" for x in search_fields]
    return "SELECT {} FROM {} WHERE {}".format(
        ",".join(fields),
        tablename,
        " AND ".join(wheres)
    )
    

OBSNIGHT_FIELDS = ['survey', 'observatory', 'telescope', 'camera', 'obsdate', 'operator', 'limiting_magnitude', 'directory']
OBSNIGHT_SEARCH_FIELDS=['survey', 'observatory', 'telescope', 'camera', 'obsdate']
OBSNIGHT_FIELDS_PK = ['night_id'] + OBSNIGHT_FIELDS

SURVEYFIELD_FIELDS = ['surveyfield_code', 'mjd', 'ra', 'declination', 'night_id']
SURVEYFIELD_FIELDS_PK = ['surveyfield_id'] + SURVEYFIELD_FIELDS


FOLLOWUP_FIELDS = ["followup_code", "followup_name", "ra", "declination", "magnitude", "comment", "field_code", "night_id"]
FOLLOWUP_FIELDS_PK = ["followup_id"] + FOLLOWUP_FIELDS

USERFIELD_FIELDS = ["userfield_code", "userfield_name", "ra", "declination", "magnitude", "comment", "field_code", "night_id"]
USERFIELD_FIELDS_PK = ['userfield_id'] + USERFIELD_FIELDS

OBS_FIELDS = ["night_id", "obsfile", "obsdir"]
OBS_FIELDS_PK = ['observation_id'] + OBS_FIELDS

ASTR_FIELDS = ['astr_code', 'obstime', 'ra', 'declination', 'magnitude', 'night_id']
ASTR_FIELDS_PK = ['astr_id'] + ASTR_FIELDS

NEO_FIELDS = ['neo_code', 'obstime', 'ra', 'declination', 'magnitude', 'night_id']
NEO_FIELDS_PK = ['neo_id'] + NEO_FIELDS

OBSNIGHT_INSERT = make_insert_template("obsnight", OBSNIGHT_FIELDS_PK)
FOLLOWUP_INSERT = make_insert_template("followups", FOLLOWUP_FIELDS)
USERFIELD_INSERT = make_insert_template("userfields", USERFIELD_FIELDS)
OBS_INSERT = make_insert_template("observations", OBS_FIELDS)
SURVEYFIELD_INSERT = make_insert_template("surveyfields", SURVEYFIELD_FIELDS)
ASTR_INSERT = make_insert_template("astrometry", ASTR_FIELDS)
NEO_INSERT = make_insert_template("neo", NEO_FIELDS)

def write_directory(extracted, directory_name):
    '''
    Writes all of the information extracted from the files in the directory to the database.
    '''
    conn = sqlite3.connect("cssdb.sqlite")
    c = conn.cursor()
    logging.debug("Writing info...")

    if not obsnight_exists(c, extracted):

        night_id = write_obsnight(c, extracted, directory_name)

        for followup in extracted["followup"]:
            logging.debug("Writing followup...")
            write_followup(c, night_id, followup)

        for userfield in extracted["fields"]:
            logging.debug("Writing field...")
            write_userfield(c, night_id, userfield)

        for observation in extracted["pointing"]["Observations"]:
            logging.debug("Writing observation...")
            write_observation(c, night_id, observation, "")

        for surveyplan in extracted["surveyplan"]:
            logging.debug("Writing survey plan...")
            write_plan(c, night_id, surveyplan)

        for astr in extracted["astrometry"]:
            logging.debug("Writing astrometry...")
            write_astr(c, night_id, astr)

        for neo in extracted["neos"]:
            logging.debug("Writing neo...")
            write_neo(c, night_id, neo)

    conn.commit()
    conn.close()


def write_obsnight(c, extracted, directory_name):
    key = hash_key(get_night_key_params(extracted))
    params = (key, 
        'CSS',
        extracted['coverage']['Source'],
        extracted['control']['Telescope'],
        extracted['control']['Detector'],
        extracted['coverage']['Date'],
        extracted['pointing']['Observer'],
        extracted['coverage']['Limiting Magnitude'],
        directory_name
    )

    exec_insert(c, OBSNIGHT_INSERT, params)
    return key

def obsnight_exists(c: sqlite3.Cursor, extracted):
    query = make_search_template("obsnight", "*", OBSNIGHT_SEARCH_FIELDS)
    params = get_night_key_params(extracted)

    c.execute(query, params)
    return c.fetchone()

def get_night_key_params(extracted):
    return ('CSS',
        extracted['coverage']['Source'],
        extracted['control']['Telescope'],
        extracted['control']['Detector'],
        extracted['coverage']['Date'])


def hash_key(params):
    m = hashlib.sha1()
    for param in params:
        m.update(param.encode('utf-8'))
    return m.hexdigest()

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

    c.execute(FOLLOWUP_INSERT, params)

def write_userfield(c, night_id, userfield):
    params = (
        userfield["id"],
        userfield.get("NAME", None),
        userfield["ra"],
        userfield["dec"],
        userfield.get("MAG", None),
        userfield.get("COM", None),
        userfield.get("field", None),
        night_id
    )

    c.execute(USERFIELD_INSERT, params)

def write_observation(c, night_id, obsfile, obsdir):
    params = (night_id, obsfile, obsdir)
    c.execute(OBS_INSERT, params)

def write_plan(c, night_id, plan):
    params = (
        plan["surveyfield_code"],
        plan["mjd"],
        plan["ra"],
        plan["dec"],
        night_id
    )
    c.execute(SURVEYFIELD_INSERT, params)

def write_astr(c, night_id, astr):
    params = (
        astr["code"],
        astr["date"],
        astr["ra"],
        astr["dec"],
        astr["mag"],        
        night_id
    )
    c.execute(ASTR_INSERT, params)

def write_neo(c, night_id, neo):
    params = (
        neo["code"],
        neo["date"],
        neo["ra"],
        neo["dec"],
        neo["mag"],        
        night_id
    )
    c.execute(NEO_INSERT, params)


def exec_insert_key(c, sql, params):
    c.execute(sql, params)
    c.execute("select last_insert_rowid()")
    return c.fetchone()[0]

def exec_insert(c, sql, params):
    c.execute(sql, params)
