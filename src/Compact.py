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
import threading
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
    maxneigh = 121

# Read objects
reader = csv.reader(open(objectListFile,'rU'))
voxels = []
for index, line in enumerate(reader):
    if index > 0:
        voxel = {}
        voxel['coords'] = numpy.array([[line[1], line[2], line[3]]])
        voxel['newcoords'] = numpy.full((1, 2), -1)
        voxel['volume'] = line[4]
        voxel['values'] = numpy.array([[line[5], line[7]]])
        voxel['visited'] = False
        voxels.append(voxel)

ncount = len(voxels)

# Create coordinate matrix and object list
matrix = numpy.empty([ncount, 2])
for index in range(0, ncount):
    matrix[index] = voxels[index]['coords'][0, 0:2:1]

# Compute distances
tree = scipy.spatial.cKDTree(matrix)
distances, neighbors = tree.query(matrix, k=maxneigh)

sys.setrecursionlimit(100000)
numpy.set_printoptions(threshold='1024')

class NuclearCluster():
    
    ### Init data structures ###
    def __init__(self, matrix, distances, neighbors, width, height):
        self.matrix = matrix
        self.distances = distances
        self.neighbors = neighbors        
        self.n_items = self.neighbors.shape[0]
        self.max_neigh = self.neighbors.shape[1]
        self.width = width
        self.height = height        
        self.target = numpy.full( \
            (int(self.width), int(self.height)), -1, dtype=int)
        self.coordinates = numpy.full((self.n_items, 2), -1, dtype=int)
        self.visited = numpy.zeros((self.n_items, 1), dtype=bool)
        self.score = 0


    ### Calculate relative position of the neighbor ###
    def nposition(self, item, neigh):
        A = self.matrix[item]
        B = self.matrix[neigh]
        BA = B - A
        C = (numpy.round(BA / numpy.linalg.norm(BA))).astype(int)
        
        return C


    ### Fill neighborhood recursively ###
    def nfill(self, x, y, item):
        self.target[x, y] = item
        self.coordinates[item] = numpy.array([x, y])
        self.visited[item] = True
        
        for n_no in range(1, self.max_neigh):
            neigh = self.neighbors[item][n_no]
            if neigh >= self.n_items:
                break
            if self.visited[neigh]:
                continue

            C = self.nposition(item, neigh)
            Cx = C[0]
            Cy = C[1]

            if self.target[x + Cx, y + Cy] == -1:
                self.nfill(x + Cx, y + Cy, neigh)


    ### Find items that have not been placed ###
    def missing(self):
        list = numpy.arange(self.n_items)
        placed = numpy.empty(0, dtype=int)
        for item in range(0, self.n_items):
            if self.coordinates[item][0] != -1 and \
                self.coordinates[item][1] != -1:
                placed = numpy.append(placed, item)
        missing = numpy.delete(list, placed)
        numpy.random.shuffle(missing)
        
        return missing
    
    
    
    def place(self, items):
        for item in items:
            W = self.anchor(item)
            print(self.best_axis(W[0], W[1]))
            
    
    ### Find a place for an item in the matrix ###
    def anchor(self, item):
        for n_no in range(1, maxneigh):
            neigh = neighbors[item][n_no]
            nx = self.coordinates[neigh][0]
            ny = self.coordinates[neigh][1]
            if nx != -1 and ny != -1:
                break;
        
        C = self.nposition(neigh, item)
        Cx = C[0]
        Cy = C[1]

        x = nx + Cx if nx != -1 else -1
        y = ny + Cy if ny != -1 else -1
            
        return numpy.array([x, y])
    
    
    ### What is the best axis to displace when placing the item ###
    def best_axis(self, x, y):
        for nx in range(x, -1, -1):
            if self.target[nx, y] == -1:
                break
        for px in range(x, self.width):
            if self.target[px, y] == -1:
                break
        for ny in range(y, -1, -1):
            if self.target[x, ny] == -1:
                break
        for py in range(y, self.height):
            if self.target[x, py] == -1:
                break
        
        V = numpy.array([x - nx, px - x, y - ny, py - y])
        axis = numpy.argmin(V)
        
        return {
            0: numpy.array([-V[0], 0]),
            1: numpy.array([V[1], 0]),
            2: numpy.array([0, -V[2]]),
            3: numpy.array([0, V[3]])
        }.get(axis, numpy.array([0, 0]))
        
        
    ### Initiate neighborhood fill sequence ###
    def fill(self):
        seed = numpy.random.randint(0, self.n_items)
        self.nfill(int(self.width/2), int(self.height/2), seed)
        self.place(self.missing())


cluster = NuclearCluster(matrix, distances, neighbors, width, height)
cluster.fill()



#for iterations in range(0, 1):
#    
#    list = numpy.arange(ncount)
#    voxlist = copy.deepcopy(voxels)
#    target = numpy.full((int(width), int(height)), -1, dtype=int)
#    
#    ### Get initial estimate matrix by filling the neighborhood with nearest neighbors
#    sys.setrecursionlimit(100000)
#    seed = numpy.random.randint(0, ncount)
#    fill_neighborhood(int(width/2), int(height/2), list[seed], voxlist, target, matrix)
#
#    ### Check which items have been already placed
#    placed = numpy.empty(0, dtype=int)
#        
#    for x in range(0, width):
#        for y in range(0, height):
#            nucleus = target[x, y]
#            if nucleus != -1:
#                placed = numpy.append(placed, nucleus)
#                
#    missing = numpy.delete(list, placed)
#    numpy.random.shuffle(missing)
#    
#    for i in range(0, len(missing)):
#        item = missing[i]
#        for neighno in range(1, maxneigh):
#            neigh = neighbors[item][neighno]
#            nx = voxlist[neigh]['newcoords'][0][0]
#            ny = voxlist[neigh]['newcoords'][0][1]
#            if nx != -1 and ny != -1:
#                break;
#        
#        C = neigh_position(item, neigh, matrix)
#        Cx = -C[0]
#        Cy = -C[1]
#        
#        if nx != -1 and ny != -1:
#            x = nx + Cx
#            y = ny + Cy
#        else:
#            x = -1
#            y = -1
#        
#        print("%i: %i %i of %i: %i %i" % (item, Cx, Cy, neigh, x, y))
#        
#    
#    
#    minx = width
#    miny = height
#    maxx = 0
#    maxy = 0
#
#    for x in range(0, 1024):
#        for y in range(0, 1024):
#            if target[x, y] != -1:
#                if x < minx:
#                    minx = x
#                if x > maxx:
#                    maxx = x
#                if y < miny:
#                    miny = y
#                if y > maxy:
#                    maxy = y
#
#    rwidth = maxx - minx + 1
#    rheight = maxy - miny + 1
#
#    rmatrix = numpy.full((rwidth, rheight), -1, dtype=int)
#
#
#    for rx in range(minx, maxx+1):
#        for ry in range(miny, maxy+1):
#            rmatrix[rx - minx, ry - miny] = target[rx, ry]
#
#    print("The matrix contains %i out of %i nuclei" % (nplaced, ncount))
