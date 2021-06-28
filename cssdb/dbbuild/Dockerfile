from alpine

run apk update
run apk add sqlite python3

run mkdir /usr/local/cssdb

copy catalina_json.tar.gz /usr/local/cssdb
copy build_db.sh /usr/local/cssdb
copy cssdb_schema.sql /usr/local/cssdb
copy cssdb_indexes.sql /usr/local/cssdb
copy cssdb.py /usr/local/cssdb
copy import_json.py /usr/local/cssdb

workdir /usr/local/cssdb
entrypoint ./build_db.sh
