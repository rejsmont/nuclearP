import sys
import os

sys.path.append("/Users/u0078517/src/ImageProcessing/nuclearP")

### These are required in development environment
import Options
reload(Options)
import Deconvolve
reload(Deconvolve)
import Segment
reload(Segment)
import Measure3D
reload(Measure3D)

### Regular imports
from ij import IJ
from ij.io import DirectoryChooser, OpenDialog, FileSaver
from ij.measure import ResultsTable
from ij.plugin import Duplicator
from Options import getOptions, getDefaults
from Deconvolve import deconvolveImage
from Segment import getProbabilityMap, segmentImage
from Measure3D import run3Dmeasurements, getResultsTable


def runSimulation(gaussXY, gaussZ, image, probabilityMap, results):

	print "Testing segmentation with blur" + \
					" x=" + "%f" % gaussXY + \
					" y=" + "%f" % gaussXY + \
					" z=" + "%f" % gaussZ

	results.incrementCounter()
	results.addValue("GX", gaussXY)
	results.addValue("GY", gaussXY)
	results.addValue("GZ", gaussZ)

	duplicator = Duplicator()
	inputPM = duplicator.run(probabilityMap)
	inputPM.setTitle("Gauss_segment_input")
	
	### Blur nuclei probability map to smoothen segmentation
	IJ.run(inputPM, "Gaussian Blur 3D...",
		" x=" + "%f" % gaussXY + \
		" y=" + "%f" % gaussXY + \
		" z=" + "%f" % gaussZ);

	### Segment image using nuclear probability map
	print ">>> Segmenting image..."
	segmentedImage = segmentImage(inputPM, None, options)
	outputName =  "OMG_XY" + "%f" % gaussXY + "_Z" + "%f" % gaussZ + "_" + inputName
	saver = FileSaver(segmentedImage)
	saver.saveAsTiffStack(outputDir + "Segmented/" + outputName + ".tif")
	print ">>> Saved " + outputDir + "Segmented/" + outputName + ".tif"

	### Get object measurements
	print ">>> Measuring objects..."
	objects = run3Dmeasurements(segmentedImage, image)
	ranges = [0, 0, 0, 0, 0]
	
	for index, particle in enumerate(objects):
		ranges[0] = ranges[0] + 1
		volume = particle['vol']
		if volume <= 500:
			ranges[1] = ranges[1] + 1
		elif volume > 500 and volume <= 1000:
			ranges[2] = ranges[2] + 1
		elif volume > 1000 and volume <= 1500:
			ranges[3] = ranges[3] + 1
		else:
			ranges[4] = ranges[4] + 1

	results.addValue("TOTAL", ranges[0])
	results.addValue("0-500", ranges[1])
	results.addValue("501-1000", ranges[2])
	results.addValue("1001-1500", ranges[3])
	results.addValue(">1500", ranges[4])
	

### Hard-set variables for testing
inputDir = "/Users/u0078517/Desktop/Samples/"
outputDir = "/Users/u0078517/Desktop/Output/"
psfFile = "/Users/u0078517/Desktop/Parameters/PSF-Venus-test.tif"
modelFile = "/Users/u0078517/Desktop/Parameters/classifier.model"

options = getDefaults()
options['modelFile'] = modelFile

options['channel'] = 0
options['regparam'] = 0.01
options['iterations'] = 50


### Initiate segmentator
segmentator = None

### Create required directories
if not os.path.exists(outputDir + "Segmented/"):
	os.makedirs(outputDir + "Segmented/")

### Loop through input images
for imageFile in os.listdir(inputDir):

	### Open file for processing
	print "Opening " + inputDir + imageFile
	image = IJ.openImage(inputDir + imageFile)
	options = getOptions(options, image)
	title = image.getTitle()
	title = title[:title.rfind('.')]
	inputName = "C" + "%i" % options['channel'] + "-" + title

	### Open probability map
	print "Opening PM " + outputDir + "Maps/PM1_" + inputName + ".tif"
	probabilityMap = IJ.openImage(outputDir + "Maps/PM1_" + inputName + ".tif")

	### Setup simulation parameters
	gaussXYmin = 0
	gaussZmin = 0
	gaussXYmax = 3
	gaussXYstep = 1
	gaussZsteps = 1
	divider = 1 / gaussXYstep * gaussZsteps

	### Setup results table
	results = ResultsTable()
	results.showRowNumbers(False)
	
	### The Simulation loop
	for gaussXY in range(gaussXYmin, gaussXYmax * divider, gaussXYstep * divider):
		if gaussXY > 0:
			for gaussZ in range (gaussZmin, gaussXY + gaussXY / gaussZsteps, gaussXY / gaussZsteps):
				runSimulation(gaussXY / divider, gaussZ / divider, image, probabilityMap, results)
		else:
			gaussZ = gaussXY
			runSimulation(gaussXY / divider, gaussZ / divider, image, probabilityMap, results)

	results.show("Gaussian optimisation")
