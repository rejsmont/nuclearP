#! /usr/bin/python

from __future__ import division
from __future__ import print_function

__author__ = "Radoslaw Kamil Ejsmont"
__date__ = "$Jul 23, 2015 4:39:56 PM$"

import os
import sys
import csv
import copy
import argparse
import numpy
import numpy.linalg
import numpy.random
import threading
import scipy.spatial
import time

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

def nCPUs():
    """
    Detects the number of CPUs on a system.
    http://python-3-patterns-idioms-test.readthedocs.org/en/latest/MachineDiscovery.html
    """
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
            # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else: # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
    # Windows:
    if os.environ.has_key("NUMBER_OF_PROCESSORS"):
            ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
            if ncpus > 0:
                return ncpus
    return 1

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
            (self.width, self.height), -1, dtype=int)
        self.coordinates = numpy.full((self.n_items, 2), -1, dtype=int)
        self.visited = numpy.zeros((self.n_items, 1), dtype=bool)


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
        self.coordinates[item, 0] = x
        self.coordinates[item, 1] = y
        self.visited[item] = True
                
        for n_no in range(1, self.max_neigh):
            neigh = self.neighbors[item, n_no]
            if neigh >= self.n_items:
                break
            if self.visited[neigh]:
                continue

            C = self.nposition(item, neigh)
            Cx = C[0]
            Cy = C[1]
            
            if Cx >= self.width or Cy > self.height:
                continue
            
            if self.target[x + Cx, y + Cy] == -1:
                self.nfill(x + Cx, y + Cy, neigh)


    ### Find items that have not been placed ###
    def missing(self):
        list = numpy.arange(self.n_items)
        placed = numpy.empty(0, dtype=int)
        for item in range(0, self.n_items):
            if self.coordinates[item, 0] != -1 and \
                self.coordinates[item, 1] != -1:
                placed = numpy.append(placed, item)
        missing = numpy.delete(list, placed)
        numpy.random.shuffle(missing)
        
        return missing
    
    
    ### Plase missing items into target matrix
    def place(self, items):
        for item in items:
            W = self.anchor(item)
            T = self.best_axis(W[0], W[1])
            
            if T[0] != 0:
                self.target[:, W[1]] = \
                    self.insert(item, self.target[:, W[1]], W[0], T[0])
            if T[1] != 0:
                self.target[W[0], :] = \
                    self.insert(item, self.target[W[0], :], W[1], T[1])
        
        for x in range(0, self.width):
            for y in range(0, self.height):
                item = self.target[x, y]
                if item != -1:
                    self.coordinates[item, 0] = x
                    self.coordinates[item, 1] = y
    
    
    ### Insert value into a specified position in vector
    def insert(self, value, vector, position, shift):
        shape = vector.shape
        result = numpy.full((shape[0]), -1, dtype=int)
        start = 0
        current = 0  
        
        if shift < 0:
            for x in range(start, position + shift):
                result[current] = vector[x]
                current = current + 1
            start = position + shift + 1
        
        for x in range(start, position):
            result[current] = vector[x]
            current = current + 1
        
        result[current] = value
        current = current + 1
        start = position
        
        if shift > 0:
            for x in range(start, position + shift):
                result[current] = vector[x]
                current = current + 1
            start = position + shift + 1
        
        for x in range(start, shape[0]):
            result[current] = vector[x]
            current = current + 1
        
        return result

    
    ### Find a place for an item in the matrix ###
    def anchor(self, item):
        for n_no in range(1, maxneigh):
            neigh = neighbors[item, n_no]
            nx = self.coordinates[neigh, 0]
            ny = self.coordinates[neigh, 1]
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
        nx = px = x
        ny = py = y
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
    
    
    ### Compact the target matrix
    def compact(self):
        minx = numpy.amin(self.coordinates[:, 0])
        miny = numpy.amin(self.coordinates[:, 1])
        maxx = numpy.amax(self.coordinates[:, 0])
        maxy = numpy.amax(self.coordinates[:, 1])
        rwidth = maxx - minx + 1
        rheight = maxy - miny + 1
        rmatrix = numpy.full((rwidth, rheight), -1, dtype=int)

        for rx in range(minx, maxx+1):
            for ry in range(miny, maxy+1):
                rmatrix[rx - minx, ry - miny] = self.target[rx, ry]
                
        return rmatrix
    
    
    ### Score target matrix
    def score(self):
        score = 0
        for item in range(0, self.n_items):
            ix = self.coordinates[item, 0]
            iy = self.coordinates[item, 1]
            if ix != -1 and iy != -1:
                for x in range(ix - 1, ix + 2):
                    for y in range(iy - 1, iy + 2):
                        if x == 1 and y == 1:
                            continue
                        neigh = self.target[x, y]
                        if neigh == -1:
                            score = score + 50
                            continue
                        npos = -1
                        for n in range (0, self.max_neigh):
                            if (neigh == self.neighbors[item, n]):
                                score = score + self.distances[item, n]
                                npos = n
                                break
                        if npos == -1:
                            score = score + 100
        
        return score
                                
    
    
    ### Initiate neighborhood fill sequence ###
    def fill(self):
        seed = numpy.random.randint(0, self.n_items)
        self.nfill(int(self.width/2), int(self.height/2), seed)
        self.place(self.missing())


class ClusteringWorker(threading.Thread):
    
    best_score = 0
    iterations = 0
    result = None
    clusterLock = threading.Lock()
    
    def __init__(self, matrix, distances, neighbors, width, height, maxit, id):
        threading.Thread.__init__(self)
        self.matrix = matrix
        self.distances = distances
        self.neighbors = neighbors
        self.width = width
        self.height = height
        self.maxit = maxit
        self.id = id
        
    def run(self):
        while ClusteringWorker.iterations < self.maxit:
            ClusteringWorker.clusterLock.acquire()
            ClusteringWorker.iterations = ClusteringWorker.iterations + 1
            ClusteringWorker.clusterLock.release()
            cluster = NuclearCluster(matrix, distances, neighbors, width, height)
            cluster.fill()
            score = cluster.score()
            #score = numpy.random.randint(0, 20)
            #for i in range(0, score):
            #    time.sleep(1)
            ClusteringWorker.clusterLock.acquire()
            print("Thread %i score: %f" % (self.id, score))
            if score < ClusteringWorker.best_score or ClusteringWorker.best_score == 0:
                ClusteringWorker.best_score = score
                ClusteringWorker.result = cluster
                print("New best score: %f" % (score))
            ClusteringWorker.clusterLock.release()
                
threads = []

for i in range(0, nCPUs() - 1):
    thread = ClusteringWorker(matrix, distances, neighbors, width, height, 20, i)
    thread.start()
    threads.append(thread)

for t in threads:
    t.join()

result = ClusteringWorker.result

if result != None:
    print("Success !!!")
    print("Final score is: %f" % result.score)

