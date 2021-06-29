import sqlite3
import json
from sqlite3.dbapi2 import converters

from flask import Flask, escape, request, render_template, send_file, Response, jsonify

import cssquery
import plotting


app = Flask(__name__)

DB_FILE="/data/cssdb.sqlite"

def to_dict(fields, t):
    return dict(zip(fields, t))

@app.route("/")
def root():

    return render_template('index.html.jinja', nights=cssquery.get_nights())

@app.route("/api/nights")
def api_nights():
    Response.content_type = "application/json"
    return jsonify(cssquery.get_nights())


@app.route("/night/<night_id>")
def night(night_id):
    return render_template(
        'night.html.jinja', 
        **cssquery.get_night(night_id))

@app.route("/api/night/<night_id>")
def api_night(night_id):
    return jsonify(
        **cssquery.get_night(night_id)
    )


@app.route("/object/<object_id>")
def obj(object_id):
    return render_template(
        'object.html.jinja', 
        objid=object_id,
        **cssquery.get_object(object_id))

@app.route("/api/object/<object_id>")
def api_obj(object_id):
    return jsonify(
        objid=object_id,
        **cssquery.get_object(object_id))

    
@app.route("/field/<field_id>")
def field(field_id):
    return render_template(
        'field.html.jinja', 
        field_id=field_id,
        **cssquery.get_field(field_id))

@app.route("/api/field/<field_id>")
def api_field(field_id):
    return jsonify(
        field_id=field_id,
        **cssquery.get_field(field_id))


@app.route("/img/neos/<night_id>")
def neos(night_id):
    result = cssquery.get_neos_for_night(night_id)
    surveyfields = plotting.convert_ra_decs(result)
    b = plotting.generate_coordinate_scatter_plot(surveyfields, "NEOs", "NEOs Detail")
    return Response(b.getvalue(), mimetype='image/png')

@app.route("/img/followups/<night_id>")
def followups(night_id):
    result = cssquery.get_followups_for_night(night_id)
    surveyfields = plotting.convert_ra_decs(result)
    b = plotting.generate_coordinate_scatter_plot(surveyfields, "Followups", "Followups Detail")
    
    return Response(b.getvalue(), mimetype='image/png')

@app.route("/img/userfields/<night_id>")
def userfields(night_id):
    result = cssquery.get_userfields_for_night(night_id)
    surveyfields = plotting.convert_ra_decs(result)
    b = plotting.generate_coordinate_scatter_plot(surveyfields, "User Fields", "User Fields Detail")
    
    return Response(b.getvalue(), mimetype='image/png')


@app.route("/img/survey/<night_id>")
def survey(night_id):
    result = cssquery.get_surveyfields_for_night(night_id)
    surveyfields = [(float(ra), float(dec)) for (ra, dec) in result]
    b = plotting.generate_coordinate_scatter_plot(surveyfields, "Survey Plan", "Survey Plan Detail")
    
    return Response(b.getvalue(), mimetype='image/png')


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def query(c:sqlite3.Cursor, sql:str, param):
    c.execute(sql, param)
    return c.fetchall()