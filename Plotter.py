import sys
import os
import csv
import math

### Import argparse to parse command-line arguments
import argparse

### Regular imports
from ij import IJ, ImagePlus
from ij.io import FileSaver
from ij.plugin import RGBStackMerge
from loci.plugins import BF
from mcib3d.geom import ObjectCreator3D


# Parse command line arguments
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Nuclear Segmentation with Fiji")
	parser.add_argument('--input-csv')
	parser.add_argument('--input-image')
	parser.add_argument('--output-image')
	
	args = parser.parse_args()
	referenceFile = args.input_image
	objectListFile = args.input_csv
	outputFile = args.output_image

print referenceFile
print objectListFile
print outputFile

# Open source image
try:
	image = IJ.openImage(referenceFile)
except Exception:
	images = BF.openImagePlus(referenceFile)
	image = images[0]
	
calibration = image.getCalibration()
zscale = calibration.getZ(1) / calibration.getX(1)
channels = image.getNChannels()

# Read objects
objects = csv.reader(open(objectListFile))
fmin = []
fmax = []
thrF = 50.000
sx = image.getWidth() 
sy = image.getHeight() 
sz = image.getNSlices()

spheres = []

for index, row in enumerate(objects):
	if index > 0:
		cx = int(round(float(row[1])))
		cy = int(round(float(row[2])))
		cz = int(round(float(row[3])))
		r =  int(round((float(row[4]) * zscale) ** (1.0/3.0)))
		f = []
		
		for i in range(0, channels):
			f.append(float(row[6 + 2 * i]))
		
		if (f[0] > thrF) and (cx - r >= 0) and (cy - r >= 0) and (cx + r <= sx) and (cy + r <= sy):
			for i in range(0, channels):
				if len(fmax) <= i:
					fmax.append(0)
				if len(fmin) <= i:
					fmin.append(65536)
				if f[i] > fmax[i]:
					fmax[i] = f[i]
				if f[i] < fmin[i]:
					fmin[i] = f[i]
			
			sphere = {'cx': cx, 'cy': cy, 'cz': cz, 'r': r, 'f': f}
			spheres.append(sphere)


# Plot spheres
channelImages = []

for i in range(0, channels):
	objectImage = ObjectCreator3D(sx, sy, sz)
	for sphere in spheres:
		fnorm = int(round((sphere['f'][i] - fmin[i]) / (fmax[i] - fmin[i]) * 65536.0))
		objectImage.createEllipsoid(
			sphere['cx'], sphere['cy'],	sphere['cz'],
			sphere['r'], sphere['r'], round(sphere['r'] / zscale),
			fnorm, False)
	channelImages.append(ImagePlus("Rendering C" + "%i" % (i + 1), objectImage.getStack()))

imageO = RGBStackMerge.mergeChannels(channelImages, False)

# Save result
saver = FileSaver(imageO)
saver.saveAsTiffStack(outputFile)	
print "Saved " + outputFile
