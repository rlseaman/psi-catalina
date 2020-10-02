FUNCS = {
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

def preprocess_datafile(filename):
    extension = filename.split(".")[-1]
    if extension in FUNCS:
        FUNCS[extension](filename)

def linefeed_to_crlf(filename):
    with open(filename) as f:
        lines = [x.strip() + "\r\n" for x in f.readlines()]
    with open(filename, "w") as f2:
        f2.writelines(lines)
