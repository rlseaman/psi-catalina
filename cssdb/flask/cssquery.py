import sqlite3

DB_FILE = "/data/cssdb.sqlite"


def get_nights():
    with get_connection() as conn:
        c = conn.cursor()
        return query_d(c, "select * from obsnight order by obsdate, survey, observatory, telescope")


def get_night(night_id):
    term = (night_id,)
    with get_connection() as conn:
        c = conn.cursor()

        return dict(
            night=query_d(c, "select * from obsnight where night_id = ?", term)[0],
            userfields=query_d(c, "select * from userfields where night_id = ? and userfield_name is not null", term),
            followups=query_d(c, "select * from followups where night_id = ?", term),
            observations=query_d(c, "select * from observations where night_id = ?", term),
            surveyfields=query_d(c, "select * from surveyfields where night_id = ?", term),
            neos=query_d(c, "select * from neo where night_id = ?", term),
        )


def get_object(object_id):
    objid = (object_id,)
    with get_connection() as conn:
        c = conn.cursor()

        return dict(
            userfields=query_d(c, "select * from userfields join obsnight using(night_id) where userfield_name = ?",
                               objid),
            followups=query_d(c, "select * from followups join obsnight using(night_id) where followup_name = ?",
                              objid),
            astrometries=query_d(c, "select * from astrometry join obsnight using(night_id) where astr_code = ?",
                                 objid),
            neos=query_d(c, "select * from neo join obsnight using(night_id) where neo_code = ?", objid)
        )


def get_field(field_id):
    match_param = (field_id,)
    like_param = ('%' + field_id + '%',)
    with get_connection() as conn:
        c = conn.cursor()

        return dict(
            surveyfields=query_d(c,
                                 "select * from surveyfields join obsnight using(night_id) where surveyfield_code = ?",
                                 match_param),
            followups=query_d(c, "select * from followups join obsnight using(night_id) where field_code = ?",
                              match_param),
            userfields=query_d(c, "select * from userfields join obsnight using(night_id) where comment = ?",
                               match_param),
            observations=query_d(c, "select * from observations join obsnight using(night_id) where obsfile like ?",
                                 like_param),
        )


def get_neos_for_night(night_id):
    match_param = (night_id,)
    with get_connection() as conn:
        c = conn.cursor()

        return query(c, "select ra, declination from neo where night_id = ?", match_param)


def get_followups_for_night(night_id):
    match_param = (night_id,)
    with get_connection() as conn:
        c = conn.cursor()
        return query(c, "select ra, declination from followups where night_id = ?", match_param)


def get_userfields_for_night(night_id):
    match_param = (night_id,)
    with get_connection() as conn:
        c = conn.cursor()
        return query(c, "select ra, declination from userfields where night_id = ?", match_param)


def get_surveyfields_for_night(night_id):
    match_param = (night_id,)
    with get_connection() as conn:
        c = conn.cursor()
        return query(c, "select ra, declination from surveyfields where night_id = ?", match_param)


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def query_d(c: sqlite3.Cursor, sql: str, param=()):
    c.execute(sql, param)
    return make_serializable(c.fetchall())


def query(c: sqlite3.Cursor, sql: str, param=()):
    c.execute(sql, param)
    return c.fetchall()


def make_serializable(results):
    return [dict(x) for x in results]
