# Overall ingestion process

## Catalina uploads data to processing server

upload to catalina.psi.edu

the structure of the files is INST\YEAR\DAY

the label files are located in INST\YEAR\DAY\pds4

place a file called .autoxfer in each directory

when the .autoxfer file is in the data and label file directory, it is ready for processing.

## Processing server verifies upload

check for the presence of an .autoxfer file in each directory

load the checksums from the signature.md5 file

compare the checksums of the uploaded files against the signature.md5 file.

if all of the files match, go to the next step

## Processing server prepares for ingestion

walk down each instrument directory

walk down each year directory

walk down each date directory

parse the label file for each data file, and get the file name of the data file and the logical identifier

get the software versions for the label, and validate against a whitelist

move the label and data file to an archive staging directory

generate a new collection inventory based on the files just ingested

create a new collection product with the new collection inventory. increment the version number by 1

## Processing server validates data

run the validator on each file in the archive staging directory

save the validation results to a reporting directory

## Processing server transfers data to archive server

rsync the archive staging directory to the archive server

this will include the newly created data files, along with the updated collection files

## Processing server places upload status marker in upload staging area

this directory will be accessible to to the catalina team