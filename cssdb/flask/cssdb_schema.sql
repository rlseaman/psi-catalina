CREATE TABLE obsnight(
    night_id integer PRIMARY KEY, 
    survey TEXT, 
    observatory TEXT, 
    telescope TEXT, 
    camera TEXT, 
    obsdate TEXT,
    operator TEXT,
    limiting_magnitude NUMERIC, 
    directory TEXT,
    mbs INTEGER
);

CREATE TABLE followups(
    followup_id INTEGER PRIMARY KEY, 
    followup_code TEXT,
    followup_name TEXT,
    ra TEXT,
    declination TEXT,
    magnitude TEXT,
    comment TEXT,
    field_code TEXT,
    night_id integer REFERENCES obsnight(night_id)
);
CREATE INDEX ix_followups_obsnight on followups(night_id);

CREATE TABLE observations(
    observation_id integer PRIMARY KEY, 
    night_id integer REFERENCES obsnight(night_id), 
    obsfile text,
    obsdir text
);
CREATE INDEX ix_observations_obsnight on observations(night_id);

CREATE TABLE userfields(
    userfield_id INTEGER PRIMARY KEY, 
    userfield_code TEXT,
    userfield_name TEXT,
    ra TEXT,
    declination TEXT,
    magnitude TEXT,
    comment TEXT,
    field_code TEXT,
    night_id INTEGER references obsnight(night_id)
);
CREATE INDEX ix_userfields_obsnight on userfields(night_id);

CREATE TABLE surveyfields(
    surveyfield_id INTEGER PRIMARY KEY, 
    surveyfield_code TEXT,
    mjd NUMERIC,    
    ra TEXT,
    declination TEXT,
    night_id INTEGER references obsnight(night_id)
);
CREATE INDEX ix_surveyfields_obsnight on surveyfields(night_id);

CREATE TABLE astrometry(
    astr_id INTEGER PRIMARY KEY, 
    astr_code TEXT,
    obstime TEXT,    
    ra TEXT,
    declination TEXT,
    magnitude TEXT,
    night_id INTEGER references obsnight(night_id)
);
CREATE INDEX ix_astrometry_obsnight on astrometry(night_id);

CREATE TABLE neo(
    neo_id INTEGER PRIMARY KEY, 
    neo_code TEXT,
    obstime TEXT,    
    ra TEXT,
    declination TEXT,
    magnitude TEXT,
    night_id INTEGER references obsnight(night_id)
);
CREATE INDEX ix_neo_obsnight on neo(night_id);
