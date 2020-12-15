import sqlite3
import json
import io
from PIL import Image, ImageDraw
from flask import Flask, escape, request, render_template, send_file, Response

import cssdb

app = Flask(__name__)

DB_FILE="cssdb.sqlite"

def to_dict(fields, t):
    return dict(zip(fields, t))

@app.route("/")
def root():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("select * from obsnight")
        obsnights = [to_dict(cssdb.OBSNIGHT_FIELDS_PK, x) for x in c.fetchall()]

    return render_template('index.html', nights=obsnights)

@app.route("/night/<night_id>")
def night(night_id):
    term = (night_id, )
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        c.execute("select * from obsnight where night_id = ?", term)
        night = [to_dict(cssdb.OBSNIGHT_FIELDS_PK, x) for x in c.fetchall()][0]

        
        c.execute("select * from userfields where night_id = ?", term)
        userfields = [to_dict(cssdb.USERFIELD_FIELDS_PK, x) for x in c.fetchall()]

        c.execute("select * from followups where night_id = ?", term)
        followups = [to_dict(cssdb.FOLLOWUP_FIELDS_PK, x) for x in c.fetchall()]

        c.execute("select * from observations where night_id = ?", term)
        observations = [to_dict(cssdb.OBS_FIELDS_PK, x) for x in c.fetchall()]

        c.execute("select * from surveyfields where night_id = ?", term)
        surveyfields = [to_dict(cssdb.SURVEYFIELD_FIELDS_PK, x) for x in c.fetchall()]

        c.execute("select * from neo where night_id = ?", term)
        neos = [to_dict(cssdb.NEO_FIELDS_PK, x) for x in c.fetchall()]


    return render_template(
        'night.html', 
        night=night, 
        userfields=userfields, 
        followups=followups, 
        observations=observations, 
        surveyfields=surveyfields,
        neos=neos)

@app.route("/object/<object_id>")
def obj(object_id):
    objid = (object_id, )
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        c.execute("select * from userfields join obsnight using(night_id) where userfield_name = ?", objid)
        userfields = [to_dict(cssdb.USERFIELD_FIELDS_PK + cssdb.OBSNIGHT_FIELDS, x) for x in c.fetchall()]

        c.execute("select * from followups join obsnight using(night_id) where followup_name = ?", objid)
        followups = [to_dict(cssdb.FOLLOWUP_FIELDS_PK + cssdb.OBSNIGHT_FIELDS, x) for x in c.fetchall()]

        c.execute("select * from astrometry join obsnight using(night_id) where astr_code = ?", objid)
        astrometries = [to_dict(cssdb.ASTR_FIELDS_PK + cssdb.OBSNIGHT_FIELDS, x) for x in c.fetchall()]

        c.execute("select * from neo join obsnight using(night_id) where neo_code = ?", objid)
        neos = [to_dict(cssdb.NEO_FIELDS_PK + cssdb.OBSNIGHT_FIELDS, x) for x in c.fetchall()]

    return render_template(
        'object.html', 
        objid=object_id,
        night=night, 
        userfields=userfields, 
        followups=followups, 
        astrometries=astrometries, 
        neos=neos)
    
@app.route("/field/<field_id>")
def field(field_id):
    match_param = (field_id, )
    like_param = ('%' + field_id + '%', )
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        c.execute("select * from surveyfields join obsnight using(night_id) where surveyfield_code = ?", match_param)
        surveyfields = [to_dict(cssdb.SURVEYFIELD_FIELDS_PK + cssdb.OBSNIGHT_FIELDS, x) for x in c.fetchall()]

        c.execute("select * from followups join obsnight using(night_id) where field_code = ?", match_param)
        followups = [to_dict(cssdb.FOLLOWUP_FIELDS_PK + cssdb.OBSNIGHT_FIELDS, x) for x in c.fetchall()]

        c.execute("select * from userfields join obsnight using(night_id) where comment = ?", match_param)
        userfields = [to_dict(cssdb.USERFIELD_FIELDS_PK + cssdb.OBSNIGHT_FIELDS, x) for x in c.fetchall()]

        c.execute("select * from observations join obsnight using(night_id) where obsfile like ?", like_param)
        observations = [to_dict(cssdb.OBS_FIELDS_PK + cssdb.OBSNIGHT_FIELDS, x) for x in c.fetchall()]



    return render_template(
        'field.html', 
        field_id=field_id,
        surveyfields=surveyfields,
        userfields=userfields,
        followups=followups,
        observations=observations)

@app.route("/img/survey/<night_id>")
def survey(night_id):
    match_param = (night_id, )
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        c.execute("select ra, declination from surveyfields where night_id = ?", match_param)
        surveyfields = [(float(ra), float(dec)) for (ra, dec) in c.fetchall()]

    coordinates = [(ra, 90 - dec) for (ra, dec) in surveyfields]

    im = Image.new("RGB", (360, 180))
    d = ImageDraw.Draw(im)
    d.point(coordinates, fill=(255,255,255))

    b = io.BytesIO()
    #im.save('temp.png', format='PNG')
    im.save(b, format='png')
    
    #return str(len(b.getvalue()))
    #return send_file('temp.png', mimetype='image/png')
    return Response(b.getvalue(), mimetype='image/png')
