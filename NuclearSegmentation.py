import sys
import os

sys.path.append("/Users/u0078517/src/ImageProcessing/nuclearP")

# These are required in development environment
import Options
reload(Options)
import Deconvolve
reload(Deconvolve)
import Segment
reload(Segment)
import Measure3D
reload(Measure3D)

# Regular imports
from ij import IJ
from Options import getOptions, getDefaults
from Deconvolve import deconvolveImage
from Segment import getProbabilityMap, segmentImage
from Measure3D import run3Dmeasurements, getResultsTable


# Get input dir / output dir / model file from user

#inputDialog = DirectoryChooser("Please select a directory contaning your images")
#outputDialog = DirectoryChooser("Please select a directory to save your results")
#modelDialog = OpenDialog("Please select the psf image")
#psfDialog = OpenDialog("Please select the model file")

#inputDir = inputDialog.getDirectory()
#outputDir = outputDialog.getDirectory()
#modelFile = modelDialog.getPath()



inputDir = "/Users/u0078517/Desktop/Samples/"
outputDir = "/Users/u0078517/Desktop/Output/"
psfDir = "/Users/u0078517/Desktop/Parameters"
psfFile = "PSF-Venus-test.tif"
modelFile = "/Users/u0078517/Desktop/Parameters/classifier.model"

options = getDefaults()
options['outputDir'] = outputDir
options['modelFile'] = modelFile

options['channel'] = 0
options['regparam'] = 0.01
options['iterations'] = 50

segmentator = None
psf = IJ.openImage(psfDir + "/" + psfFile)

for imageFile in os.listdir(inputDir):

	print "Opening " + inputDir + imageFile
	
	image = IJ.openImage(inputDir + imageFile)
	options = getOptions(options, image)

	print "Deconvolving image..."
	deconvolvedImage = deconvolveImage(image, psf, options)

	print "Calculating probability maps..."
	probabilityMap = getProbabilityMap(deconvolvedImage, image, segmentator, 1, options)

	# Blur probability map to smoothen segmentation
	IJ.run(probabilityMap, "Gaussian Blur 3D...", "x=2 y=2 z=1");

	print "Segmenting image..."
	segmentedImage = segmentImage(probabilityMap, None, image, options)

	print "Measuring objects..."
	measurements = run3Dmeasurements(segmentedImage, image)
	results = getResultsTable(measurements, image, options)

	print "Image " + imageFile + " processed!"
	
psf.close()
