#!/usr/bin/env sh
uwsgi --plugins http,python --http 0.0.0.0:8080 --uid 100 --master --module app:app  --processes ${WORKERS:-16}