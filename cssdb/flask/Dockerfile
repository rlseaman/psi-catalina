from alpine

run apk update
run apk add sqlite python3 py3-flask uwsgi uwsgi-python uwsgi-http py3-matplotlib

run mkdir /usr/local/cssdb


copy *.py /usr/local/cssdb/
copy *.sh /usr/local/cssdb/
copy static /usr/local/cssdb/static
copy templates /usr/local/cssdb/templates


workdir /usr/local/cssdb
#./uwsgi --http 127.0.0.1:8080 --master --module mywsgiapp --processes 4
entrypoint ./run.sh

