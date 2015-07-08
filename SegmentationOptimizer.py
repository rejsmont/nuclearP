import sys
import os

sys.path.append("C:\\Users\\rejsmont\\nuclearP")

### These are required in development environment
import Options
reload(Options)
import Segmentation
reload(Segmentation)
import Analysis
reload(Analysis)

### Regular imports
from ij import IJ
from ij.io import DirectoryChooser, OpenDialog, FileSaver
from ij.measure import ResultsTable
from ij.plugin import Duplicator
from Options import getOptions, getDefaults
from Segmentation import Segmentator
from Analysis import Analyzer
from mcib3d.image3d import ImageInt

def runSimulation(options, image, probabilityMap, results):
	
	print "Testing segmentation with blur" + \
					" x=" + "%f" % options['gaussXY'] + \
					" y=" + "%f" % options['gaussXY'] + \
					" z=" + "%f" % options['gaussZ'] + \
					" localBackground="  + "%i" % options['localBackground'] + \
					" seedRadius="  + "%i" % options['seedRadius']

	results.incrementCounter()
	results.addValue("Threshold", options['localBackground'])
	results.addValue("Seed radius", options['seedRadius'])
	results.addValue("GX", options['gaussXY'])
	results.addValue("GY", options['gaussXY'])
	results.addValue("GZ", options['gaussZ'])

	duplicator = Duplicator()
	inputPM = duplicator.run(probabilityMap)
	inputPM.setTitle("Gauss_segment_input")
	
	### Blur nuclei probability map to smoothen segmentation
	IJ.run(inputPM, "Gaussian Blur 3D...",
		" x=" + "%f" % options['gaussXY'] + \
		" y=" + "%f" % options['gaussXY'] + \
		" z=" + "%f" % options['gaussZ'])

	### Segment image using nuclear probability map
	print ">>> Segmenting image..."
	segmentator = Segmentator(options, "Segmented")
	segmentedImage = segmentator.process(inputPM)
	outputName = "OMG_XY" + ("%f" % options['gaussXY']) + "_Z" + ("%f" % options['gaussZ']) + \
		"_TH" + ("%i" % options['localBackground']) + \
		"_SR" + ("%i" % options['seedRadius']) + \
		"_" + inputName
	segmentator.save(segmentedImage, outputName)

	### Get object measurements
	print ">>> Measuring objects..."
	ranges = [0, 0, 0, 0, 0, 0, 0, 0]
	analyzer = Analyzer(options, segmentator.objects, "Results")
	segmented = ImageInt.wrap(segmentedImage)
	for objectV in analyzer.objects.getObjectsList():
		if (options['edgeXY'] and options['edgeZ']) or \
			(not objectV.edgeImage(segmented, not options['edgeXY'], not options['edgeZ'])):
			ranges[0] = ranges[0] + 1
			volume = objectV.getVolumePixels()
			if volume <= 250:
				ranges[1] = ranges[1] + 1
			elif volume > 250 and volume <= 500:
				ranges[2] = ranges[2] + 1
			elif volume > 500 and volume <= 750:
				ranges[3] = ranges[3] + 1
			elif volume > 750 and volume <= 1000:
				ranges[4] = ranges[4] + 1
			elif volume > 1000 and volume <= 1500:
				ranges[5] = ranges[5] + 1
			else:
				ranges[6] = ranges[6] + 1
		else:
			ranges[7] = ranges[7] + 1
			
	results.addValue("TOTAL", ranges[0])
	results.addValue("0-250", ranges[1])
	results.addValue("251-500", ranges[2])
	results.addValue("501-750", ranges[3])
	results.addValue("751-1000", ranges[4])
	results.addValue("1001-1500", ranges[5])
	results.addValue(">1500", ranges[6])
	results.addValue("Skipped", ranges[7])
	

### Hard-set variables for testing
inputDir =  "E:\\rejsmont\\nuclearP\\samples\\"
outputDir = "E:\\rejsmont\\nuclearP\\output\\"
psfFile = "E:\\rejsmont\\nuclearP\\parameters\\PSF-Venus-test.tif"
modelFile = "E:\\rejsmont\\nuclearP\\parameters\\classifier.model"

options = getDefaults()
options['inputDir'] = inputDir
options['outputDir'] = outputDir
options['modelFile'] = modelFile

options['channel'] = 0
options['regparam'] = 0.01
options['iterations'] = 50

options['edgeXY'] = False
options['edgeZ'] = False

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
	print "Opening PM " + options['outputDir'] + "Maps\\PM1_" + inputName + ".tif"
	probabilityMap = IJ.openImage(options['outputDir'] + "Maps\\PM1_" + inputName + ".tif")

	### Setup simulation parameters
	thresholdMin = 4096
	thresholdMax = 36864
	thresholdStep = 4096
	seedMin = 2
	seedMax = 13
	seedStep = 2
	gaussXYmin = 0
	gaussZmin = 0
	gaussXYmax = 5.2
	gaussXYstep = 0.2
	gaussZsteps = 5
	divider = 1 / gaussXYstep * gaussZsteps

	### Setup results table
	results = ResultsTable()
	results.showRowNumbers(False)
	
	### The Simulation loop
	for threshold in range(thresholdMin, thresholdMax, thresholdStep):
		for seed in range(seedMin, seedMax, seedStep):
			for gaussXY in range(gaussXYmin, gaussXYmax * divider, gaussXYstep * divider):
				if gaussXY > 0:
					for gaussZ in range (gaussZmin, gaussXY + gaussXY / gaussZsteps, gaussXY / gaussZsteps):
						options['gaussXY'] = gaussXY / divider
						options['gaussZ'] = gaussZ / divider
						options['localBackground'] = threshold
						options['seedRadius'] = seed
						runSimulation(options, image, probabilityMap, results)
				else:
					gaussZ = gaussXY
					options['gaussXY'] = gaussXY / divider
					options['gaussZ'] = gaussZ / divider
					options['localBackground'] = threshold
					options['seedRadius'] = seed
					runSimulation(options, image, probabilityMap, results)

	results.show("Optimisation results")
	results.save(options['outputDir'] + "OptimizationResults" + ".csv")
