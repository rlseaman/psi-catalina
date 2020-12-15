def make_insert_template(tablename, fields):
    return "INSERT INTO {}({}) VALUES ({})".format(
        tablename,
        ",".join(fields),
        ",".join(["?"] * len(fields))
    )

OBSNIGHT_FIELDS = ['survey', 'observatory', 'telescope', 'camera', 'obsdate', 'operator', 'limiting_magnitude', 'directory']
OBSNIGHT_FIELDS_PK = ['night_id'] + OBSNIGHT_FIELDS

SURVEYFIELD_FIELDS = ['surveyfield_code', 'mjd', 'ra', 'declination', 'night_id']
SURVEYFIELD_FIELDS_PK = ['surveyfield_id'] + SURVEYFIELD_FIELDS


FOLLOWUP_FIELDS = ["followup_code", "followup_name", "ra", "declination", "magnitude", "comment", "field_code", "night_id"]
FOLLOWUP_FIELDS_PK = ["followup_id"] + FOLLOWUP_FIELDS

USERFIELD_FIELDS = ["userfield_code", "userfield_name", "ra", "declination", "magnitude", "comment", "field_code", "night_id"]
USERFIELD_FIELDS_PK = ['userfield_id'] + USERFIELD_FIELDS

OBS_FIELDS = ["night_id", "obsfile"]
OBS_FIELDS_PK = ['observation_id'] + OBS_FIELDS

ASTR_FIELDS = ['astr_code', 'obstime', 'ra', 'declination', 'magnitude', 'night_id']
ASTR_FIELDS_PK = ['astr_id'] + ASTR_FIELDS

NEO_FIELDS = ['neo_code', 'obstime', 'ra', 'declination', 'magnitude', 'night_id']
NEO_FIELDS_PK = ['neo_id'] + NEO_FIELDS

OBSNIGHT_INSERT = make_insert_template("obsnight", OBSNIGHT_FIELDS)
FOLLOWUP_INSERT = make_insert_template("followups", FOLLOWUP_FIELDS)
USERFIELD_INSERT = make_insert_template("userfields", USERFIELD_FIELDS)
OBS_INSERT = make_insert_template("observations", OBS_FIELDS)
SURVEYFIELD_INSERT = make_insert_template("surveyfields", SURVEYFIELD_FIELDS)
ASTR_INSERT = make_insert_template("astrometry", ASTR_FIELDS)
NEO_INSERT = make_insert_template("neo", NEO_FIELDS)