#! /usr/bin/env python3
'''
Handles processing inventory files. This includes reading, writing,
and merging inventories.
'''
import os
import iotools

INVENTORY_FILENAME_TEMPLATE = 'collection_{collection_id}_{major}.{minor}.csv'


def write_inventory(inventory, collection_lidvid, collection_dir):
    '''
    Writes the collection inventory to a file
    '''
    collection_filename = INVENTORY_FILENAME_TEMPLATE.format(**collection_lidvid)
    collection_path = os.path.join(collection_dir, collection_filename)
    iotools.write_file(collection_path, '\r\n'.join(inventory) + '\r\n')

def read_inventory(collection_lidvid, collection_dir):
    '''
    Reads in the inventory for the most recent collection update before this one
    '''
    if collection_lidvid['major']:
        collection_filename = INVENTORY_FILENAME_TEMPLATE.format(**collection_lidvid)
        collection_path = os.path.join(collection_dir, collection_filename)
        return open(collection_path).readlines()
    return []

def from_lidvids(member_type, product_lidvids):
    '''
    Generates an inventory from a list of product lidvids
    '''
    return [member_type + ',' + x for x in product_lidvids]

def merge(old_inv, new_inv):
    '''
    Merges two inventories together. There is no collision resolution yet.
    '''
    return new_inv + old_inv
