import sqlite3
import json
import io
from sqlite3.dbapi2 import converters
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from flask import Flask, escape, request, render_template, send_file, Response

import cssquery


app = Flask(__name__)

DB_FILE="/data/cssdb.sqlite"

def to_dict(fields, t):
    return dict(zip(fields, t))

@app.route("/")
def root():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("select * from obsnight order by obsdate")
        obsnights = c.fetchall()

    return render_template('index.html', nights=obsnights)

@app.route("/night/<night_id>")
def night(night_id):
    night, userfields, followups, observations, surveyfields, neos = cssquery.get_night(night_id)

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
    userfields, followups, astrometries, neos = cssquery.get_object(object_id)
    
    return render_template(
        'object.html', 
        objid=object_id,
        userfields=userfields, 
        followups=followups, 
        astrometries=astrometries, 
        neos=neos)
    
@app.route("/field/<field_id>")
def field(field_id):
    surveyfields, followups, userfields, observations = cssquery.get_field(field_id)
    
    return render_template(
        'field.html', 
        field_id=field_id,
        surveyfields=surveyfields,
        userfields=userfields,
        followups=followups,
        observations=observations)

@app.route("/img/neos/<night_id>")
def neos(night_id):
    result = cssquery.get_neos_for_night(night_id)
    surveyfields = convert_ra_decs(result)
    b = generate_coordinate_scatter_plot(surveyfields, "NEOs", "NEOs Detail")
    return Response(b.getvalue(), mimetype='image/png')

@app.route("/img/followups/<night_id>")
def followups(night_id):
    match_param = (night_id, )
    result = cssquery.get_followups_for_night(night_id)
    surveyfields = convert_ra_decs(result)
    b = generate_coordinate_scatter_plot(surveyfields, "Followups", "Followups Detail")
    
    return Response(b.getvalue(), mimetype='image/png')

@app.route("/img/userfields/<night_id>")
def userfields(night_id):
    result = cssquery.get_userfields_for_night(night_id)
    surveyfields = convert_ra_decs(result)
    b = generate_coordinate_scatter_plot(surveyfields, "User Fields", "User Fields Detail")
    
    return Response(b.getvalue(), mimetype='image/png')


@app.route("/img/survey/<night_id>")
def survey(night_id):
    result = cssquery.get_surveyfields_for_night(night_id)
    surveyfields = [(float(ra), float(dec)) for (ra, dec) in result]
    b = generate_coordinate_scatter_plot(surveyfields, "Survey Plan", "Survey Plan Detail")
    
    return Response(b.getvalue(), mimetype='image/png')

def generate_coordinate_scatter_plot(coordinates, main_label, detail_label):
    ras = [coordinate[0] for coordinate in coordinates]
    decs = [coordinate[1] for coordinate in coordinates]
    fig = Figure(figsize=(10, 5))

    summary = fig.add_subplot(1,2,1)
    summary.set_xlabel("Right Ascension (degrees)")
    summary.set_ylabel("Declination (degrees)")
    summary.set_title(main_label)
    summary.set_xlim(0,360)
    summary.set_ylim(-90, 90)
    summary.scatter(ras, decs, s=3, color='blue', alpha=0.5)

    detail = fig.add_subplot(1,2,2)
    detail.set_xlabel("Right Ascension (degrees)")
    detail.set_ylabel("Declination (degrees)")
    detail.set_title(detail_label)
    detail.scatter(ras, decs, s=3, color='blue', alpha=0.5)


    b = io.BytesIO()
    FigureCanvas(fig).print_png(b)
    return b

def parse_triplet(val):
    hd, m, s = split_triplet(val)
    return int(hd), int(m), float(s)

def split_triplet(val):
    return val.split(":") if ":" in val else val.split(" ")

def ra_hms_to_dec(hours, minutes, seconds):
    #return (hours/24.0*360.0) + (minutes/24.0/60.0*360.0) + (seconds/24.0/60.0/60.0*360.0)
    return hours * 15.0 + minutes / 4.0 + seconds / 240.0

def dec_dms_to_dec(degrees, minutes, seconds):
    return degrees + (minutes/60.0) + (seconds/3600.0)

def convert_ra_decs(values):
    return [(ra_hms_to_dec(*parse_triplet(ra)), dec_dms_to_dec(*parse_triplet(dec))) for (ra, dec) in values if ra and dec]

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def query(c:sqlite3.Cursor, sql:str, param):
    c.execute(sql, param)
    return c.fetchall()