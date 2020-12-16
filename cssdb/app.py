import sqlite3
import json
import io
from PIL import Image, ImageDraw
from flask import Flask, escape, request, render_template, send_file, Response


app = Flask(__name__)

DB_FILE="cssdb.sqlite"

def to_dict(fields, t):
    return dict(zip(fields, t))

@app.route("/")
def root():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("select * from obsnight")
        obsnights = c.fetchall()

    return render_template('index.html', nights=obsnights)

@app.route("/night/<night_id>")
def night(night_id):
    term = (night_id, )
    with get_connection() as conn:
        c = conn.cursor()

        night = query(c, "select * from obsnight where night_id = ?", term)[0]
        userfields = query(c, "select * from userfields where night_id = ?", term)
        followups = query(c, "select * from followups where night_id = ?", term)
        observations = query(c, "select * from observations where night_id = ?", term)
        surveyfields = query(c, "select * from surveyfields where night_id = ?", term)
        neos = query(c, "select * from neo where night_id = ?", term)

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
    with get_connection() as conn:
        c = conn.cursor()

        userfields = query(c, "select * from userfields join obsnight using(night_id) where userfield_name = ?", objid)
        followups = query(c, "select * from followups join obsnight using(night_id) where followup_name = ?", objid)
        astrometries = query(c, "select * from astrometry join obsnight using(night_id) where astr_code = ?", objid)
        neos = query(c, "select * from neo join obsnight using(night_id) where neo_code = ?", objid)

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
    with get_connection() as conn:
        c = conn.cursor()

        surveyfields = query(c, "select * from surveyfields join obsnight using(night_id) where surveyfield_code = ?", match_param)
        followups = query(c, "select * from followups join obsnight using(night_id) where field_code = ?", match_param)
        userfields = query(c, "select * from userfields join obsnight using(night_id) where comment = ?", match_param)
        observations = query(c, "select * from observations join obsnight using(night_id) where obsfile like ?", like_param)

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
    with get_connection() as conn:
        c = conn.cursor()

        result = query(c, "select ra, declination from surveyfields where night_id = ?", match_param)
        surveyfields = [(float(ra), float(dec)) for (ra, dec) in result]

    coordinates = [(ra, 90 - dec) for (ra, dec) in surveyfields]

    b = generate_coordinate_plot(coordinates)
    
    #return str(len(b.getvalue()))
    #return send_file('temp.png', mimetype='image/png')
    return Response(b.getvalue(), mimetype='image/png')

def generate_coordinate_plot(coordinates):
    im = Image.new("RGB", (360, 180))
    d = ImageDraw.Draw(im)
    d.point(coordinates, fill=(255,255,255))
    b = io.BytesIO()
    #im.save('temp.png', format='PNG')
    im.save(b, format='png')
    return b


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def query(c:sqlite3.Cursor, sql:str, param):
    c.execute(sql, param)
    return c.fetchall()