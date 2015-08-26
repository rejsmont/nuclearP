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
    width = 32 #args.width
    height = 32 #args.height

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
        voxel['neighno'] = 0
        voxel['visited'] = False
        voxels.append(voxel)

# Create coordinate matrix and object list
matrix = numpy.empty([len(voxels), 2])
list = numpy.arange(len(voxels))

for index in range(0, len(voxels)):
    matrix[index] = voxels[index]['coords'][0, 0:2:1]

# Compute distances
tree = scipy.spatial.cKDTree(matrix)
distances, neighbors = tree.query(matrix, k=25)


### Check if neighbor's spot is free
def can_reference(x, y, item, neigh, voxels):
    
    x1 = x + 1
    y1 = y + 1
    x2 = -x + 1
    y2 = -y + 1
    
    if voxels[item]['neighs'][x1, y1] != -1:
        if voxels[item]['neighs'][x1, y1] != neigh:
            return False
        else:
            return None
    
    if voxels[neigh]['neighs'][x2, y2] != -1:
        if voxels[neigh]['neighs'][x2, y2] != item:
            return False
        else:
            return None
    
    return True

### Check if neighbor's neighbors conflict with item's neighbors
def can_merge(Cx, Cy, item, neigh, voxels):
    updates = [] 
    positions = get_overlap(Cx, Cy) 
    for pos in positions:
        current = voxels[item]['neighs'][pos['x'] + 1, pos['y'] + 1]
        if current != -1:
            Zx = -pos['x'] + Cx
            Zy = -pos['y'] + Cy
            result = can_reference(Zx, Zy, current, neigh, voxels)
            if result is True :
                it = {}
                it['x'] = Zx
                it['y'] = Zy
                it['item'] = current
                it['neigh'] = neigh
                updates.append(it)
            elif result is None:
                continue
            else:
                return False
    return updates

### Which part of the neighborhood do we share with our neighbor
def get_overlap(Cx, Cy): 
    positions = []
    if abs(Cx) + abs(Cy) == 2:
        pos = {}
        pos['x'] = Cx
        pos['y'] = 0
        positions.append(pos)
        pos = {}
        pos['x'] = 0
        pos['y'] = Cy
        positions.append(pos)
    elif abs(Cx) + abs(Cy) == 1:
        if Cx == 0:
            for x in [-1, 1]:
                for y in [Cy, 0]:
                    pos = {}
                    pos['x'] = x
                    pos['y'] = y
                    positions.append(pos)
        else:
            for x in [Cx, 0]:
                for y in [-1, 1]:
                    pos = {}
                    pos['x'] = x
                    pos['y'] = y
                    positions.append(pos)
    return positions


### Reference this neighbor
def reference_neighbor(x, y, item, neigh, voxels):
    
    x1 = x + 1
    y1 = y + 1
    x2 = -x + 1
    y2 = -y + 1
    
    if voxels[item]['neighs'][x1, y1] != neigh:
        voxels[item]['neighs'][x1, y1] = neigh
        voxels[item]['neighno'] = voxels[item]['neighno'] + 1
    if voxels[neigh]['neighs'][x2, y2] != item:
        voxels[neigh]['neighs'][x2, y2] = item
        voxels[neigh]['neighno'] = voxels[item]['neighno'] + 1

### Adopt neighbor's neighbors as our own
def update_references(items, voxels):
    
    for item in items:
        reference_neighbor(item['x'], item['y'], \
            item['item'], item['neigh'], voxels)


def fill_neighborhood(cx, cy, item, voxels, target):
    target[cx, cy] = item
    voxels[item]['visited'] = True
    print(voxels[item]['neighs'])
    for x in range(-1, 2):
        for y in range(-1, 2):
            rx = cx + x
            ry = cy + y
            current = voxels[item]['neighs'][x + 1, y + 1]
            if current != -1 and not voxels[current]['visited']:
                fill_neighborhood(rx, ry, current, voxels, target)
                

worklist = copy.deepcopy(list)
numpy.random.shuffle(worklist)
voxlist = copy.deepcopy(voxels)
keepgoing = True

while True:
    worklist = copy.deepcopy(list)
    numpy.random.shuffle(worklist)
    voxlist = copy.deepcopy(voxlist)
    for item in worklist:
        for nord in range(1, 25):
            if voxlist[item]['neighno'] >= 8:
                continue
            neigh = neighbors[item][nord]
            A = matrix[item]
            B = matrix[neigh]
            BA = B - A
            C = (numpy.round(BA / numpy.linalg.norm(BA))).astype(int)
            Cx = C[0]
            Cy = C[1]

            if can_reference(Cx, Cy, item, neigh, voxlist):
                refs_item = can_merge(Cx, Cy, item, neigh, voxlist)
                refs_neigh = can_merge(-Cx, -Cy, neigh, item, voxlist)
                if refs_item is not False and refs_neigh is not False:
                    reference_neighbor(Cx, Cy, item, neigh, voxlist)
                    update_references(refs_item, voxlist)
                    update_references(refs_neigh, voxlist)

    complete = 0
    orphans = 0
    total = 0
    for i in range(0, len(worklist)):
        if voxlist[i]['neighno'] == 0:
            orphans = orphans + 1
        if voxlist[i]['neighno'] == 8:
            complete = complete + 1
        total = total + 1

    print("Total: %i, complete: %i, orphans: %i" % (total, complete, orphans))
    if orphans == 0:
        break;

i = 0
neighs = voxlist[worklist[i]]['neighno']
while (neighs < 8) and (i < len(worklist)):
    i = i + 1
    neighs = voxlist[worklist[i]]['neighno']

target = numpy.full((int(width), int(height)), -1, dtype=int)
fill_neighborhood(int(width/2), int(height/2), worklist[i], voxlist, target)

xmin = width
ymin = height
xmax = 0
ymax = 0

sumX = numpy.full((int(width)), 0, dtype=int)
sumY = numpy.full((int(height)), 0, dtype=int)

placed = 0
for x in range(0, int(width)):
    for y in range(0, int(height)):
        sumX[x] = sumX[x] + target[x,y] + 1
        sumY[y] = sumY[y] + target[x,y] + 1
        if (target[x,y] >= 0):
            placed = placed + 1

previous = 0
for i in range(0, width):
    current = sumX[i]
    if current != previous:
        if current >= 0 and i < xmin:
            xmin = i
        if current == 0 and i > xmax:
            xmax = i - 1
        previous = current

previous = 0
for i in range(0, height):
    current = sumY[i]
    if current != previous:
        if current >= 0 and i < ymin:
            ymin = i
        if current == 0 and i > ymax:
            ymax = i - 1
        previous = current

print("Total: %i, placed: %i" % (total, placed))
print("xmin(%i), ymin(%i), xmax(%i), ymax(%i)" % (xmin, ymin, xmax, ymax))
