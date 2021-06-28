#! /usr/bin/env sh

set -e

if [ -e /data/cssdb.sqlite ]; then
    rm /data/cssdb.sqlite
    
fi

sqlite3 /data/cssdb.sqlite < cssdb_schema.sql

if [ -n "$PROD" ]; then
    echo "Downloading fresh data..."
    rm catalina_json.tar.gz
    wget https://sbnarchive.psi.edu/pds4/surveys/catalina_sync/catalina_json.tar.gz
fi

tar -xzf catalina_json.tar.gz
find json -name "*.json" -exec python3 import_json.py --filename '{}' \; 
sqlite3 /data/cssdb.sqlite < cssdb_indexes.sql