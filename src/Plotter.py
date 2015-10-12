#! /usr/bin/fiji

### Python imports
import csv
import math
import argparse

### ImageJ / Jython imports
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from ij.plugin import RGBStackMerge
from ij.process import ShortProcessor
from loci.plugins import BF
from mcib3d.geom import ObjectCreator3D


# Parse command line arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nuclear Segmentation with Fiji")
    parser.add_argument('--input-csv')
    parser.add_argument('--input-image')
    parser.add_argument('--output-image')
    parser.add_argument('--flat')
    parser.add_argument('--pixels')
    parser.add_argument('--width')
    parser.add_argument('--height')

    args = parser.parse_args()
    referenceFile = args.input_image
    objectListFile = args.input_csv
    outputFile = args.output_image
    if args.flat:
        if str(args.flat).upper() == "TRUE":
            flat = True
	else:
            flat = False
    else:
	flat = False
    if args.pixels:
        if str(args.pixels).upper() == "TRUE":
            pixels = True
            width = int(args.width)
            height = int(args.height)
	else:
            pixels = False
    else:
	pixels = False

    if flat and pixels:
        print("Both --flat and --pixels cannot be specified simultaneously.")
        sys.exit(1)

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
		r =  int(round(((float(row[4]) * 0.75 * (1/math.pi)) ** (1.0/3.0)) * zscale))
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

if flat == True:
    for i in range(0, channels):
	imageProcessor = ShortProcessor(sx*4, sy*4)
	imageStack = ImageStack(sx*4, sy*4)
        for sphere in spheres:
            fnorm = int(round((sphere['f'][i] - fmin[i]) / (fmax[i] - fmin[i]) * 65536.0))
            x = sphere['cx'] * 4 - sphere['r']
            y = sphere['cy'] * 4 - sphere['r']
            d = sphere['r'] * 2
            imageProcessor.setValue(fnorm)
            imageProcessor.fillOval(x, y, d, d)
	imageStack.addSlice(imageProcessor)
	channelImages.append(ImagePlus("Rendering C" + "%i" % (i + 1), imageStack))
		
    imageO = RGBStackMerge.mergeChannels(channelImages, False)
elif pixels == True:
    for i in range(0, channels):
	imageProcessor = ShortProcessor(width, height)
	imageStack = ImageStack(width, height)
        for sphere in spheres:
            fnorm = int(round((sphere['f'][i] - fmin[i]) / (fmax[i] - fmin[i]) * 65536.0))
            x = sphere['cx']
            y = sphere['cy']
            d = sphere['r'] * 2
            imageProcessor.putPixel(x, y, fnorm)
	imageStack.addSlice(imageProcessor)
	channelImages.append(ImagePlus("Rendering C" + "%i" % (i + 1), imageStack))
	
    imageO = RGBStackMerge.mergeChannels(channelImages, False)
else:
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
