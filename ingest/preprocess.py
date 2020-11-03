import subprocess
import logging

def linefeed_to_crlf(filename):
    logging.info("Normalizing whitespace for: %s", filename)
    with open(filename) as f:
        lines = [x.strip() + "\r\n" for x in f.readlines()]
    with open(filename, "w") as f2:
        f2.writelines(lines)

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
    newfilename = decompress(filename)
    extension = newfilename.split(".")[-1]
    if extension in DATA_FUNCS:
        DATA_FUNCS[extension](newfilename)

def preprocess_labelfile(filename, datafilenames):
    with open(filename) as f:
        labelcontents = f.read()

    for datafilename in datafilenames:
        extension = datafilename.split(".")[-1]
        if extension in LABEL_FUNCS:
            labelcontents = LABEL_FUNCS[extension](labelcontents, datafilename)

    with open(filename, "w") as f2:
        f2.write(labelcontents)
    

def decompress(datafilename):
    if datafilename.endswith(".gz"):
        logging.info("Decompressing: %s", datafilename)
        temp_data_path = datafilename.replace(".gz", "")
        subprocess.run(['gunzip', temp_data_path])
        return temp_data_path
    else:
        return datafilename
