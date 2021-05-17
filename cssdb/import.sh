#! /usr/bin/env bash
set -e

SCRIPT_DIR=`dirname $0`
#rm cssdb.sqlite && sqlite3 cssdb.sqlite < cssdb_schema.sql

DATE=$1
YEAR=$2

pushd $SCRIPT_DIR

python3 extract_all.py --basedir=/data/CSS --nights=21 --outfilebase=/data/json
find /data/json -name '*.json' -exec python3 import_json.py --filename '{}' \;
find /data/json -name '*.json' -exec trash '{}' \;

popd