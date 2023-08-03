import logging
import os
import gzip
from typing import IO, Iterable


def has_compressed(filename: str) -> bool:
    return os.path.exists(f"{filename}.gz")


def file_open(filename: str, mode: str = "rt") -> IO:
    logging.debug(f"Opening: {filename} with mode: {mode}")
    if filename.endswith(".gz"):
        return gzip.open(filename, mode)
    return open(filename, mode)


def linefeed_to_crlf(filename: str) -> None:
    """
    Normalize the line feeds in a data file, replacing them with CRLFs
    """

    logging.info(f"Normalizing whitespace for: {filename}")
    if has_compressed(filename):
        logging.debug(f"Using compressed version: {filename}")
        filename = f"{filename}.gz"

    with file_open(filename) as f:
        lines = [x.strip("\r\n") for x in f.readlines()]

    os.rename(filename, f"{filename}.bak")

    with file_open(filename, "wt") as f2:
        f2.write("\r\n".join(lines) + "\r\n")

    os.remove(f"{filename}.bak")


def strip_label_fz_extension(contents: str, datafilename: str) -> str:
    uncompressed_datafilename = datafilename.replace(".fz", "")
    return contents.replace(datafilename, uncompressed_datafilename)


def strip_label_gz_extension(contents: str, datafilename: str) -> str:
    uncompressed_datafilename = datafilename.replace(".gz", "")
    return contents.replace(datafilename, uncompressed_datafilename)


DATA_FUNCS = {
}

LABEL_FUNCS = {
    "fz": strip_label_fz_extension,
    "gz": strip_label_gz_extension
}


def preprocess_datafile(filename: str) -> None:
    """
    Preprocesses the file. If the file is of an appropriate type
    (defined by membership in DATA_FUNCS), decompress the file,
    run the preprocessing routine indicated in DATA_FUNCS, and
    recompress the file.
    """
    newfilename = filename.replace(".gz", "")
    extension = newfilename.split(".")[-1]

    if extension in DATA_FUNCS:
        DATA_FUNCS[extension](filename)


def preprocess_labelfile(filename: str, datafilenames: Iterable[str]) -> None:
    """
    Preproesses the label. If the file is of an appropriate type
    (defined in LABEL_FUNCS), apply the appropriate transformation
    to the contents. In most cases, this will remove the gz of fz
    extensions from the data file names.
    """
    with open(filename) as f:
        labelcontents = f.read()

    for datafilename in datafilenames:
        extension = datafilename.split(".")[-1]
        if extension in LABEL_FUNCS:
            labelcontents = LABEL_FUNCS[extension](labelcontents, datafilename)

    os.rename(filename, f"{filename}.bak")

    with open(filename, "w") as f2:
        f2.write(labelcontents)
