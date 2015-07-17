import sys
import os

sys.path.append("/Users/u0078517/src/ImageProcessing/nuclearP")

### These imports are required in development environment
import Options
reload(Options)
import Analysis
reload(Analysis)

options = Options.getDefaults()
options['outputDir'] = "/tmp/"

### Regular imports
from ij import IJ, ImagePlus
from ij.io import DirectoryChooser, OpenDialog, FileSaver
from ij.plugin import ChannelSplitter
from Analysis import Analyzer

imageFile = "/Users/u0078517/Desktop/sample.tif"
objectMapFile = "/Users/u0078517/Desktop/objects.tif"

def process(imageFile, objectMapFile):
	
	image = IJ.openImage(imageFile)
	objects = IJ.openImage(objectMapFile)

	### Get object measurements
	print "Measuring objects..."
	analyzer = Analyzer(options, objects, "Results")
	results = analyzer.getMeasurements(image)
	results.show("Results")
	
	### This should be it!
	print "Image " + imageFile + " processed!"
	
	return objects

process(imageFile, objectMapFile)
