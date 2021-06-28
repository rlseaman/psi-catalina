CREATE INDEX ix_astrometry_obsnight on astrometry(night_id);
CREATE INDEX ix_neo_obsnight on neo(night_id);
CREATE INDEX ix_surveyfields_obsnight on surveyfields(night_id);
CREATE INDEX ix_userfields_obsnight on userfields(night_id);
CREATE INDEX ix_observations_obsnight on observations(night_id);
CREATE INDEX ix_followups_obsnight on followups(night_id);
