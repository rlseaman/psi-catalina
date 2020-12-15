#! /usr/bin/env bash
set -e

rm cssdb.sqlite && sqlite3 cssdb.sqlite < cssdb_schema.sql


python3 import.py data/CSS/703/2019/19Aug21
python3 import.py data/CSS/703/2019/19Aug22
python3 import.py data/CSS/703/2019/19Aug25
python3 import.py data/CSS/703/2019/19Aug26
python3 import.py data/CSS/703/2019/19Aug27
python3 import.py data/CSS/703/2019/19Aug28
python3 import.py data/CSS/703/2019/19Aug30


python3 import.py data/CSS/G96/2019/19Aug20
python3 import.py data/CSS/G96/2019/19Aug21
python3 import.py data/CSS/G96/2019/19Aug22
python3 import.py data/CSS/G96/2019/19Aug25
python3 import.py data/CSS/G96/2019/19Aug26
python3 import.py data/CSS/G96/2019/19Aug27

python3 import.py data/CSS/I52/2019/19Aug21
python3 import.py data/CSS/I52/2019/19Aug25
python3 import.py data/CSS/I52/2019/19Aug26
python3 import.py data/CSS/I52/2019/19Aug27
python3 import.py data/CSS/I52/2019/19Aug28
python3 import.py data/CSS/I52/2019/19Aug30

python3 import.py data/CSS/V06/2019/19Aug30
python3 import.py data/CSS/V06/2019/19Sep01
python3 import.py data/CSS/V06/2019/19Sep02
