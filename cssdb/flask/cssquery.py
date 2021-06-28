import sqlite3
DB_FILE="/data/cssdb.sqlite"

def get_night(night_id):
    term = (night_id, )
    with get_connection() as conn:
        c = conn.cursor()

        night = query(c, "select * from obsnight where night_id = ?", term)[0]
        userfields = query(c, "select * from userfields where night_id = ? and userfield_name is not null", term)
        followups = query(c, "select * from followups where night_id = ?", term)
        observations = query(c, "select * from observations where night_id = ?", term)
        surveyfields = query(c, "select * from surveyfields where night_id = ?", term)
        neos = query(c, "select * from neo where night_id = ?", term)

    return (night, userfields, followups, observations, surveyfields, neos)

def get_object(object_id):
    objid = (object_id, )
    with get_connection() as conn:
        c = conn.cursor()

        userfields = query(c, "select * from userfields join obsnight using(night_id) where userfield_name = ?", objid)
        followups = query(c, "select * from followups join obsnight using(night_id) where followup_name = ?", objid)
        astrometries = query(c, "select * from astrometry join obsnight using(night_id) where astr_code = ?", objid)
        neos = query(c, "select * from neo join obsnight using(night_id) where neo_code = ?", objid)

        return (userfields, followups, astrometries, neos)

def get_field(field_id):
    match_param = (field_id, )
    like_param = ('%' + field_id + '%', )
    with get_connection() as conn:
        c = conn.cursor()

        surveyfields = query(c, "select * from surveyfields join obsnight using(night_id) where surveyfield_code = ?", match_param)
        followups = query(c, "select * from followups join obsnight using(night_id) where field_code = ?", match_param)
        userfields = query(c, "select * from userfields join obsnight using(night_id) where comment = ?", match_param)
        observations = query(c, "select * from observations join obsnight using(night_id) where obsfile like ?", like_param)

    return surveyfields, followups, userfields, observations

def get_neos_for_night(night_id):
    match_param = (night_id, )
    with get_connection() as conn:
        c = conn.cursor()

        return query(c, "select ra, declination from neo where night_id = ?", match_param)

def get_followups_for_night(night_id):
    match_param = (night_id, )
    with get_connection() as conn:
        c = conn.cursor()
        return query(c, "select ra, declination from followups where night_id = ?", match_param)

def get_userfields_for_night(night_id):
    match_param = (night_id, )
    with get_connection() as conn:
        c = conn.cursor()
        return query(c, "select ra, declination from userfields where night_id = ?", match_param)

def get_surveyfields_for_night(night_id):
    match_param = (night_id, )
    with get_connection() as conn:
        c = conn.cursor()
        match_param = (night_id, )
        return query(c, "select ra, declination from surveyfields where night_id = ?", match_param)
    

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def query(c:sqlite3.Cursor, sql:str, param):
    c.execute(sql, param)
    return c.fetchall()        