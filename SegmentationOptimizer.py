import sys
import os

sys.path.append("/Users/u0078517/src/ImageProcessing/nuclearP")

### These are required in development environment
import Options
reload(Options)
import Segmentation
reload(Segmentation)
import Analysis
reload(Analysis)

### Regular imports
from threading import Thread, currentThread
from ij import IJ
from ij.io import DirectoryChooser, OpenDialog, FileSaver
from ij.measure import ResultsTable
from ij.plugin import Duplicator
from Options import getOptions, getDefaults
from Segmentation import Segmentator
from Analysis import Analyzer
from mcib3d.image3d import ImageInt
from java.util.concurrent.atomic import AtomicInteger
from java.lang import Runtime, InterruptedException

def runSimulation(options, image):
	
	print "Testing segmentation with blur" + \
					" x=" + "%f" % options['gaussXY'] + \
					" y=" + "%f" % options['gaussXY'] + \
					" z=" + "%f" % options['gaussZ'] + \
					" localBackground="  + "%i" % options['localBackground'] + \
					" seedRadius="  + "%i" % options['seedRadius']

	duplicator = Duplicator()
	inputPM = duplicator.run(image)
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
		"_" + image.getTitle
	segmentator.save(segmentedImage, outputName)

	### Get object measurements
	print ">>> Measuring objects..."
	results = {'all':0, '0':0, '250':0, '500':0, '750':0, '1000':0, '1500':0, 'edge':0}
	analyzer = Analyzer(options, segmentator.objects, "Results")
	segmented = ImageInt.wrap(segmentedImage)
	for objectV in analyzer.objects.getObjectsList():
		if (options['edgeXY'] and options['edgeZ']) or \
			(not objectV.edgeImage(segmented, not options['edgeXY'], not options['edgeZ'])):
			results['all'] = results['all'] + 1
			volume = objectV.getVolumePixels()
			if volume <= 250:
				results['0'] = results['0'] + 1
			elif volume > 250 and volume <= 500:
				results['250'] = results['250'] + 1
			elif volume > 500 and volume <= 750:
				results['500'] = results['500'] + 1
			elif volume > 750 and volume <= 1000:
				results['750'] = results['750'] + 1
			elif volume > 1000 and volume <= 1500:
				results['1000'] = results['1000'] + 1
			else:
				results['1500'] = results['1500'] + 1
		else:
			results['edge'] = results['edge'] + 1
	
	return results

### Hard-set variables for testing
options = getDefaults()
options['inputFile'] = "/Users/u0078517/Desktop/Output/Maps/PM1_C0-E2C-disc-1-sample.tif"
options['outputDir'] = "/Users/u0078517/Desktop/Output/"
options['channel'] = 0
options['regparam'] = 0.01
options['iterations'] = 50
options['edgeXY'] = True
options['edgeZ'] = False

### Simulation options
options['thresholdMin'] = 4096
options['thresholdMax'] = 36864
options['thresholdStep'] = 4096
options['seedMin'] = 2
options['seedMax'] = 13
options['seedStep'] = 2
options['gaussXYmin'] = 0
options['gaussXYmax'] = 5.2
options['gaussXYstep'] = 0.2
options['gaussZmin'] = 0
options['gaussZsteps'] = 5

### Open probability map
image = IJ.openImage(options['inputFile'])
divider = 1 / options['gaussXYstep'] * options['gaussZsteps']

### Generate parameter array
parameters = []
results = []
for threshold in range(options['thresholdMin'], options['thresholdMax'], options['thresholdStep']):
	for seed in range(options['seedMin'], options['seedMax'], options['seedStep']):
		for gaussXY in range(options['gaussXYmin'] * divider, \
			options['gaussXYmax'] * divider, \
			options['gaussXYstep'] * divider):
			if gaussXY > 0:
				for gaussZ in range (options['gaussZmin'], \
					gaussXY + gaussXY / options['gaussZsteps'], \
					gaussXY / options['gaussZsteps']):
					opts = {}
					opts['gaussXY'] = gaussXY / divider
					opts['gaussZ'] = gaussZ / divider
					opts['localBackground'] = threshold
					opts['seedRadius'] = seed
					parameters.append(opts)
					res = {}
					results.append(res)
			else:
				gaussZ = gaussXY
				opts = {}
				opts['gaussXY'] = gaussXY / divider
				opts['gaussZ'] = gaussZ / divider
				opts['localBackground'] = threshold
				opts['seedRadius'] = seed
				parameters.append(opts)
				res = {}
				results.append(res)

ncpus = Runtime.getRuntime().availableProcessors()

print "Generated " + "%i" % len(parameters) + " parameters and will fill " + "%i" % len(results) + " results"
print "Detected " + "%i" % ncpus + " CPUs"

counter = AtomicInteger(0)
threads = []

def runThread(parameters, options, image, results):

	index = counter.getAndIncrement()
	while index < len(parameters):
		thread = currentThread()
		opts = options.copy()
		opts.update(parameters[index])
		res = runSimulation(opts, image)
		results[index].update(res)
		index = counter.getAndIncrement()
		
	return None

for i in range(0, ncpus):
	threads.append(Thread(target=lambda: runThread(parameters, options, image, results)))

for i in range(0, len(threads)):
	threads[i].start()

for i in range(0, len(threads)):
	threads[i].join()

resultsTable = ResultsTable()
resultsTable.showRowNumbers(False)

for i in range(0, len(parameters)):
	resultsTable.incrementCounter()
	resultsTable.addValue("Threshold", parameters[i]['localBackground'])
	resultsTable.addValue("Seed radius", parameters[i]['seedRadius'])
	resultsTable.addValue("GX", parameters[i]['gaussXY'])
	resultsTable.addValue("GY", parameters[i]['gaussXY'])
	resultsTable.addValue("GZ", parameters[i]['gaussZ'])
	resultsTable.addValue("TOTAL", results[i]['all'])
	resultsTable.addValue("0-250", results[i]['0'])
	resultsTable.addValue("251-500", results[i]['250'])
	resultsTable.addValue("501-750", results[i]['500'])
	resultsTable.addValue("751-1000", results[i]['750'])
	resultsTable.addValue("1001-1500", results[i]['1000'])
	resultsTable.addValue(">1501", results[i]['1500'])
	resultsTable.addValue("Skipped", results[i]['edge'])

resultsTable.show("Optimisation results")
resultsTable.save(options['outputDir'] + "OptimizationResults" + ".csv")
