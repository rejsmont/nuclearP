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
import collections
import multiprocessing
import numpy
import numpy.linalg
import numpy.random
import scipy.spatial
import random
import Queue

### Cluster nuclei using kD-tree approach
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
        self.ccoords = numpy.full((self.n_items, 2), -1, dtype=int)
        self.visited = numpy.zeros((self.n_items, 1), dtype=bool)
        self.seed = 0
        self.score = 0
        self.size = 0


    ### Calculate distance to the neighbor ###
    def __ndistance(self, item, neigh):
        A = self.matrix[item]
        B = self.matrix[neigh]
        BA = B - A
        C = numpy.linalg.norm(BA)
        
        return C

    ### Calculate relative position of the neighbor ###
    def __nposition(self, item, neigh):
        A = self.matrix[item]
        B = self.matrix[neigh]
        BA = B - A
        C = (numpy.round(BA / numpy.linalg.norm(BA))).astype(int)
        
        return C
    
    ### Iterative version of nfill ###
    def __nfill_s(self, x, y, item):
        
        stack = collections.deque()

        self.target[x, y] = item
        self.coordinates[item, 0] = x
        self.coordinates[item, 1] = y
        self.visited[item] = True
        value = (x, y, item)
        stack.append(value)
        
        while stack:
            (x, y, item) = stack.pop()
            
            for n_no in range(1, self.max_neigh):
                neigh = self.neighbors[item, n_no]
                if neigh >= self.n_items:
                    break
                if self.visited[neigh]:
                    continue

                C = self.__nposition(item, neigh)
                Cx = C[0]
                Cy = C[1]

                if Cx >= self.width or Cy >= self.height or Cx < 0 or Cy < 0:
                    continue

                if self.target[x + Cx, y + Cy] == -1:
                    x = x + Cx
                    y = y + Cy
                    item = neigh
                    self.target[x, y] = item
                    self.coordinates[item, 0] = x
                    self.coordinates[item, 1] = y
                    self.visited[item] = True
                    value = (x, y, item)
                    stack.append(value)


    ### Find items that have not been placed ###
    def __missing(self):
        list = numpy.arange(self.n_items)
        placed = numpy.empty(0, dtype=int)
        for item in range(0, self.n_items):
            if self.coordinates[item, 0] != -1 and \
                self.coordinates[item, 1] != -1:
                placed = numpy.append(placed, item)
        missing = numpy.delete(list, placed)
        numpy.random.shuffle(missing)
        
        return missing
    
    
    ### Place missing items into target matrix
    def __place(self, items):
        for item in items:
            W = self.__anchor(item)
            T = self.__best_axis(W[0], W[1])
            
            if T[0] != 0:
                self.target[:, W[1]] = \
                    self.__insert(item, self.target[:, W[1]], W[0], T[0])
            if T[1] != 0:
                self.target[W[0], :] = \
                    self.__insert(item, self.target[W[0], :], W[1], T[1])
        
        for x in range(0, self.width):
            for y in range(0, self.height):
                item = self.target[x, y]
                if item != -1:
                    self.coordinates[item, 0] = x
                    self.coordinates[item, 1] = y
    
    
    ### Insert value into a specified position in vector
    def __insert(self, value, vector, position, shift):
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
    def __anchor(self, item):
        for n_no in range(1, maxneigh):
            neigh = neighbors[item, n_no]
            nx = self.coordinates[neigh, 0]
            ny = self.coordinates[neigh, 1]
            if nx != -1 and ny != -1:
                break;
        
        C = self.__nposition(neigh, item)
        Cx = C[0]
        Cy = C[1]

        x = nx + Cx if nx != -1 else -1
        y = ny + Cy if ny != -1 else -1
        
        return numpy.array([x, y])
    
    
    ### What is the best axis to displace when placing the item ###
    def __best_axis(self, x, y):
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
    def __compact(self):
        minx = numpy.amin(self.coordinates[:, 0])
        miny = numpy.amin(self.coordinates[:, 1])
        maxx = numpy.amax(self.coordinates[:, 0])
        maxy = numpy.amax(self.coordinates[:, 1])
        rwidth = maxx - minx + 1
        rheight = maxy - miny + 1
        rmatrix = numpy.full((rwidth, rheight), -1, dtype=int)

        for rx in range(minx, maxx+1):
            for ry in range(miny, maxy+1):
                item = self.target[rx, ry]
                rmatrix[rx - minx, ry - miny] = self.target[rx, ry]
                if item != -1:
                    self.ccoords[item, 0] = rx - minx
                    self.ccoords[item, 1] = ry - miny
        
        return rmatrix
    
    
    ### Score target matrix
    def __score(self):
        score = 0
        for item in range(0, self.n_items):
            ix = self.coordinates[item, 0]
            iy = self.coordinates[item, 1]
            if ix != -1 and iy != -1:
                for x in range(ix - 1, ix + 2):
                    for y in range(iy - 1, iy + 2):
                        if x >= self.width or y >= self.height \
                            or x < 0 or y < 0:
                            continue
                        if x == ix and y == iy:
                            continue
                        neigh = self.target[x, y]
                        if neigh == -1:
                            score = score + 50
                        else:
                            score = score + self.__ndistance(item, neigh)
        
        return score
    
    
    ### Initiate neighborhood fill sequence ###
    def fill(self):
        seed = random.randrange(0, self.n_items)
        self.__nfill_s(int(self.width/2), int(self.height/2), seed)
        self.__place(self.__missing())
        self.score = self.__score()
        rmatrix = self.__compact()
        self.size = rmatrix.shape[0] * rmatrix.shape[1]


class ClusteringWorker(multiprocessing.Process):
    
    best_score = 0
    best_size = 0
    result = None
    result_s = None
    
    def __init__(self, matrix, distances, neighbors, width, height,
        maxit, id, iterator, results):
        multiprocessing.Process.__init__(self)
        self.matrix = matrix
        self.distances = distances
        self.neighbors = neighbors
        self.width = width
        self.height = height
        self.maxit = maxit
        self.id = id
        self.score = 0
        self.size = 0
        self.score_result = None
        self.size_result = None
        self.iterator = iterator
        self.results = results
        
    def run(self):
        ### Some iteration variable
        print("Thread %i initial value" % self.id)
        while self.iterator.value < self.maxit:
            with self.iterator.get_lock():
                self.iterator.value += 1
            print("Thread %i currently at %i" % (self.id, self.iterator.value))
            cluster = NuclearCluster(matrix, distances, neighbors, width, height)
            cluster.fill()
            if self.score_result == None or cluster.score < self.score_result.score:
                self.score_result = cluster
            if self.size_result == None or cluster.size < self.size_result.size:
                self.size_result = cluster    
        
        print("Thread %i saving score results" % self.id)
        result = self.score_result
        rtuple = (result.score, result.size, result.ccoords)
        self.results.put(rtuple)
        
        print("Thread %i saving size results" % self.id)
        result = self.size_result
        rtuple = (result.score, result.size, result.ccoords)
        self.results.put(rtuple)
        
        print("Thread %i saved results" % self.id)
        


# Parse command line arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nuclear Segmentation with Fiji")
    parser.add_argument('--input-csv')
    parser.add_argument('--output-csv')
    parser.add_argument('--width')
    parser.add_argument('--height')
    
    args = parser.parse_args()
    objectListFile = args.input_csv
    outputFile = args.output_csv
    width = 1024 #args.width
    height = 1024 #args.height
    maxneigh = 121

    # Read objects
    reader = csv.reader(open(objectListFile,'rU'))
    voxels = []
    for index, line in enumerate(reader):
        if index > 0:
            voxel = {}
            voxel['coords'] = numpy.array([line[1], line[2], line[3]])
            voxel['newcoords'] = numpy.full((1, 2), -1)
            voxel['volume'] = line[4]
            voxel['values'] = numpy.array([line[5], line[7]])
            voxels.append(voxel)

    ncount = len(voxels)

    # Create coordinate matrix and object list
    matrix = numpy.empty([ncount, 2])
    for index in range(0, ncount):
        matrix[index] = voxels[index]['coords'][0:2:1]

    # Compute distances
    tree = scipy.spatial.cKDTree(matrix)
    distances, neighbors = tree.query(matrix, k=maxneigh)

    processes = []

    maxprocs = multiprocessing.cpu_count() - 1
    if maxprocs < 1:
        maxprocs = 1

    iterator = multiprocessing.Value('i', 0)
    lock = multiprocessing.Lock()

    results = multiprocessing.Queue()

    for i in range(0, maxprocs):
        process = ClusteringWorker(matrix, distances, neighbors,
            width, height, 20, i, iterator, results)
        processes.append(process)

    for p in processes:
        p.start()
    
    print("Waiting for jobs to finish")
    
    rlist = []
    for i in range(maxprocs*2):
        result = results.get()
        rlist.append(result)
        print("Retrieved result %i" % i+1)

    print("Result queue empty")
    
    for p in processes:
        p.join()

    print("All jobs have finished")

    
    best_score = 0
    best_size = 0
    best_score_result = None
    best_size_result = None
        
    for result in rlist:
        if result[0] < best_score or best_score == 0:
            best_score = result[0]
            best_score_result = result[2]
            print("New global best score: %f" % (best_score))
        if result[1] < best_size or best_size == 0:
            best_size = result[1]
            best_size_result = result[2]
            print("New global best size: %i" % (best_size))

    
    result = best_score_result

    with open(outputFile + ".score", 'wb') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Particle","cx","cy","cz","Volume",
            "Integral 0","Mean 0","Integral 1","Mean 1"])
        for item in range(0, len(result)):
             csvwriter.writerow([item + 1, result[item, 0], \
                result[item, 1], 0, voxels[item]['volume'], \
                voxels[item]['values'][0], \
                float(voxels[item]['values'][0]) / float(voxels[item]['volume']), \
                voxels[item]['values'][1], \
                float(voxels[item]['values'][1]) / float(voxels[item]['volume'])])

    result = best_size_result

    with open(outputFile + ".size", 'wb') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Particle","cx","cy","cz","Volume",
            "Integral 0","Mean 0","Integral 1","Mean 1"])
        for item in range(0, len(result)):
             csvwriter.writerow([item + 1, result[item, 0], \
                result[item, 1], 0, voxels[item]['volume'], \
                voxels[item]['values'][0], \
                float(voxels[item]['values'][0]) / float(voxels[item]['volume']), \
                voxels[item]['values'][1], \
                float(voxels[item]['values'][1]) / float(voxels[item]['volume'])])
