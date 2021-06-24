#! /usr/bin/env sh

set -e

if [ -e cssdb.sqlite ]; then
    rm cssdb.sqlite
    
fi

sqlite3 cssdb.sqlite < cssdb_schema.sql
wget https://sbnarchive.psi.edu/pds4/surveys/catalina_sync/catalina_json.tar.gz
tar -xzf catalina_json.tar.gz
find json -name "*.json" -exec python3 import_json.py --filename '{}' \; 
