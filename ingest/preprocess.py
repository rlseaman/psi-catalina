from genericpath import exists
import subprocess
import logging
import os
import gzip


def has_compressed(filename):
    return os.path.exists(filename + ".gz")

def file_open(filename, mode="rt"):
    logging.info("Opening: %s with mode: %s", filename, mode)
    if filename.endswith(".gz"):
        return gzip.open(filename, mode)
    return open(filename, mode)

def linefeed_to_crlf(filename):
    '''
    Normalize the line feeds in a data file, replacing them with CRLFs
    '''

    logging.info("Normalizing whitespace for: %s", filename)
    if has_compressed(filename):
        logging.info("Using compressed version: %s", filename)
        filename = filename + ".gz"

    with file_open(filename) as f:
        lines = [x.strip() for x in f.readlines()]

    os.rename(filename, filename + ".bak")

    with file_open(filename, "wt") as f2:
        f2.write("\r\n".join(lines) + "\r\n")

    os.remove(filename + ".bak")

def strip_label_fz_extension(contents, datafilename):
    uncompressed_datafilename = datafilename.replace(".fz", "")
    return contents.replace(datafilename, uncompressed_datafilename)

def strip_label_gz_extension(contents, datafilename):
    uncompressed_datafilename = datafilename.replace(".gz", "")
    return contents.replace(datafilename, uncompressed_datafilename)

DATA_FUNCS = {
    "sext": linefeed_to_crlf,
    "iext": linefeed_to_crlf,
    "strp": linefeed_to_crlf,
    "strm": linefeed_to_crlf,
    "scmp": linefeed_to_crlf,
    "ephm": linefeed_to_crlf,
    "mtds": linefeed_to_crlf,
    "mtdf": linefeed_to_crlf, 
    "dets": linefeed_to_crlf,
    "hits": linefeed_to_crlf,
    "rjct": linefeed_to_crlf,
    "mpcd": linefeed_to_crlf,
    "neos": linefeed_to_crlf,
    "fail": linefeed_to_crlf,
    "followup": linefeed_to_crlf,
    "ast": linefeed_to_crlf,   
    "userfields": linefeed_to_crlf
}

LABEL_FUNCS = {
    "fz": strip_label_fz_extension,
    "gz": strip_label_gz_extension
}

def preprocess_datafile(filename):
    '''
    Preprocesses the file. If the file is of an appropriate type 
    (defined by membership in DATA_FUNCS), decompress the file,
    run the preprocessing routine indicated in DATA_FUNCS, and
    recompress the file.
    '''
    newfilename = filename.replace(".gz", "")
    extension = newfilename.split(".")[-1]

    if extension in DATA_FUNCS:
        DATA_FUNCS[extension](filename)

def preprocess_labelfile(filename, datafilenames):
    '''
    Preproesses the label. If the file is of an appropriate type
    (defined in LABEL_FUNCS), apply the appropriate transformation
    to the contents. In most cases, this will remove the gz of fz
    extensions from the data file names.
    '''
    with open(filename) as f:
        labelcontents = f.read()

    for datafilename in datafilenames:
        extension = datafilename.split(".")[-1]
        if extension in LABEL_FUNCS:
            labelcontents = LABEL_FUNCS[extension](labelcontents, datafilename)

    os.rename(filename, filename + ".bak")

    with open(filename, "w") as f2:
        f2.write(labelcontents)
    

