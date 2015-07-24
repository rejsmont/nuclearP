#! /usr/bin/python

__author__ = "Radoslaw Kamil Ejsmont"
__date__ = "$Jul 23, 2015 4:39:56 PM$"

import csv
import argparse
import numpy

# Parse command line arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nuclear Segmentation with Fiji")
    parser.add_argument('--input-csv')
    parser.add_argument('--width')
    parser.add_argument('--height')
    
    args = parser.parse_args()
    objectListFile = args.input_csv
    width = args.width
    height = args.height

# Read objects
objects = csv.reader(open(objectListFile))

matrix = numpy.empty([height, width])

