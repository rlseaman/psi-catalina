"""
Provides short functions for handling IO.
"""
import os


def read_file(filename: str) -> str:
    """
    One-liner to read a file
    """
    with open(filename) as infile:
        return infile.read()


def write_file(filename: str, contents: str) -> None:
    """
    One-liner to write a file
    """
    path = os.path.dirname(filename)
    os.makedirs(path, exist_ok=True)
    with open(filename, "w") as outfile:
        outfile.write(contents)
