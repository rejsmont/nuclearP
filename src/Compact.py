#! /usr/bin/python

from __future__ import division
from __future__ import print_function

__author__ = "Radoslaw Kamil Ejsmont"
__date__ = "$Jul 23, 2015 4:39:56 PM$"

import sys
import csv
import copy
import argparse
import numpy
import numpy.linalg
import numpy.random
import scipy.spatial

# Parse command line arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nuclear Segmentation with Fiji")
    parser.add_argument('--input-csv')
    parser.add_argument('--width')
    parser.add_argument('--height')
    
    args = parser.parse_args()
    objectListFile = args.input_csv
    width = 1024 #args.width
    height = 1024 #args.height

# Read objects
reader = csv.reader(open(objectListFile,'rU'))
voxels = []
for index, line in enumerate(reader):
    if index > 0:
        voxel = {}
        voxel['coords'] = numpy.array([[line[1], line[2], line[3]]])
        voxel['volume'] = line[4]
        voxel['values'] = numpy.array([[line[5], line[7]]])
        voxel['neighs'] = numpy.full((3, 3), -1, dtype=int)
        voxel['neighs'][1, 1] = index - 1
        voxel['visited'] = False
        voxels.append(voxel)

ncount = len(voxels)

# Create coordinate matrix and object list
matrix = numpy.empty([len(voxels), 2])
list = numpy.arange(len(voxels))

for index in range(0, len(voxels)):
    matrix[index] = voxels[index]['coords'][0, 0:2:1]

# Compute distances
tree = scipy.spatial.cKDTree(matrix)
distances, neighbors = tree.query(matrix, k=25)

worklist = copy.deepcopy(list)
numpy.random.shuffle(worklist)
voxlist = copy.deepcopy(voxels)

target = numpy.full((int(width), int(height)), -1, dtype=int)


### Get initial estimate matrix by filling the neighborhood with nearest neighbors

def fill_neighborhood(x, y, item, voxels, target, matrix):
    target[x, y] = item
    voxels[item]['visited'] = True
    
    for neighno in range(1, 25):
        neigh = neighbors[item][neighno]
        if voxels[neigh]['visited'] == True:
            continue;
        
        A = matrix[item]
        B = matrix[neigh]
        BA = B - A
        C = (numpy.round(BA / numpy.linalg.norm(BA))).astype(int)
        Cx = C[0]
        Cy = C[1]
        
        if target[x + Cx, y + Cy] == -1:
            fill_neighborhood(x + Cx, y + Cy, neigh, voxels, target, matrix)

sys.setrecursionlimit(100000)
fill_neighborhood(int(width/2), int(height/2), worklist[0], voxlist, target, matrix)

minx = width
miny = height
maxx = 0
maxy = 0

for x in range(0, 1024):
    for y in range(0, 1024):
        if target[x, y] != -1:
            if x < minx:
                minx = x
            if x > maxx:
                maxx = x
            if y < miny:
                miny = y
            if y > maxy:
                maxy = y

rwidth = maxx - minx + 1
rheight = maxy - miny + 1

rmatrix = numpy.full((rwidth, rheight), -1, dtype=int)

nplaced = 0

for rx in range(minx, maxx+1):
    for ry in range(miny, maxy+1):
        rmatrix[rx - minx, ry - miny] = target[rx, ry]
        if target[rx, ry] != -1:
            nplaced = nplaced + 1

print("The matrix contains %i out of %i nuclei" % (nplaced, ncount))
