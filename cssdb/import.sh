#! /usr/bin/env bash
set -e

SCRIPT_DIR=`dirname $0`

pushd $SCRIPT_DIR

if [ ! -e cssdb.sqlite ]; then
    sqlite3 cssdb.sqlite < cssdb_schema.sql
fi

python3 extract_all.py --basedir=/data/ready/gbo.ast.catalina.survey/ --nights=21 --outfilebase=/data/json
find /data/json -name '*.json' -exec python3 import_json.py --filename '{}' \;
find /data/json -name '*.json' -exec trash '{}' \;

popd