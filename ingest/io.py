#! /usr/bin/env python3
'''
Provides short functions for handling IO
'''
import os

def read_file(filename):
    '''
    One-liner to read a file
    '''
    with open(filename) as infile:
        return infile.read()

def write_file(filename, contents):
    '''
    One-liner to write a file
    '''
    path = os.path.dirname(filename)
    os.makedirs(path, exist_ok=True)
    with open(filename, "w") as outfile:
        outfile.write(contents)
