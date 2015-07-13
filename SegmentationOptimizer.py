import sys
import os

### Import argparse to parse command-line arguments
import argparse

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
from Options import getOptions, getDefaults as getBaseDefaults
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

	inputName = image.getTitle()
	inputName = inputName[:inputName.rfind('.')]
	
	### Blur nuclei probability map to smoothen segmentation
	IJ.run(inputPM, "Gaussian Blur 3D...",
		" x=" + "%f" % options['gaussXY'] + \
		" y=" + "%f" % options['gaussXY'] + \
		" z=" + "%f" % options['gaussZ'])

	### Segment image using nuclear probability map
	print ">>> Segmenting image..."
	segmentator = Segmentator(options, "Segmented")
	segmentedImage = segmentator.process(inputPM)
	outputName = "OM_XY" + ("%f" % options['gaussXY']) + "_Z" + ("%f" % options['gaussZ']) + \
		"_TH" + ("%i" % options['localBackground']) + \
		"_SR" + ("%i" % options['seedRadius']) + \
		"_" + inputName
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

def getDefaults():
	options = getBaseDefaults()
	options['edgeXY'] = True
	options['edgeZ'] = False

	options['thresholdMin'] = 12288
	options['thresholdMax'] = 16384
	options['thresholdStep'] = 4096
	options['seedMin'] = 2
	options['seedMax'] = 4
	options['seedStep'] = 2
	options['gaussXYmin'] = 0
	options['gaussXYmax'] = 3
	options['gaussXYstep'] = 1
	options['gaussZmin'] = 0
	options['gaussZsteps'] = 1
	options['outputFile'] = "simulation_results.csv"
	
	return options


def makeParameters(options):
	parameters = []
	divider = 1 / options['gaussXYstep'] * options['gaussZsteps']
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
				else:
					gaussZ = gaussXY
					opts = {}
					opts['gaussXY'] = gaussXY / divider
					opts['gaussZ'] = gaussZ / divider
					opts['localBackground'] = threshold
					opts['seedRadius'] = seed
					parameters.append(opts)
	
	return parameters

options = getDefaults()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Nuclear Segmentation Optimizer")
	parser.add_argument('--input-file')
	parser.add_argument('--output-file')
	parser.add_argument('--output-dir')
	parser.add_argument('--params-out')
	parser.add_argument('--one-shot')
	parser.add_argument('--gauss-xy')
	parser.add_argument('--gauss-xy-min')
	parser.add_argument('--gauss-xy-max')
	parser.add_argument('--gauss-xy-step')
	parser.add_argument('--gauss-z')
	parser.add_argument('--gauss-z-min')
	parser.add_argument('--gauss-z-steps')
	parser.add_argument('--seg-bkgd-thr')
	parser.add_argument('--seg-bkgd-thr-min')
	parser.add_argument('--seg-bkgd-thr-max')
	parser.add_argument('--seg-bkgd-thr-step')
	parser.add_argument('--seg-seed-thr')
	parser.add_argument('--seg-seed-r')
	parser.add_argument('--seg-seed-r-min')
	parser.add_argument('--seg-seed-r-max')
	parser.add_argument('--seg-seed-r-step')
	parser.add_argument('--seg-watershed')
	parser.add_argument('--seg-vol-min')
	parser.add_argument('--seg-vol-max')
	parser.add_argument('--exclude-edge-xy')
	parser.add_argument('--exclude-edge-z')
	
	args = parser.parse_args()
	options['inputFile'] = args.input_file
	options['outputFile'] = args.output_file
	options['outputDir'] = args.output_dir
	options['paramsOut'] = args.params_out
	
	if args.gauss_xy:
		options['gaussXY'] = args.gauss_xy
	if args.gauss_xy_min:
		options['gaussXYmin'] = args.gauss_xy_min
	if args.gauss_xy_max:
		options['gaussXYmax'] = args.gauss_xy_max
	if args.gauss_xy_step:
		options['gaussXYstep'] = args.gauss_xy_step
	
	if args.gauss_z:
		options['gaussZ'] = args.gauss_z
	if args.gauss_z_min:
		options['gaussZmin'] = args.gauss_z_min
	if args.gauss_z_steps:
		options['gaussZsteps'] = args.gauss_z_steps
	
	if args.seg_bkgd_thr:
		options['localBackground'] = args.seg_bkgd_thr
	if args.seg_bkgd_thr_min:
		options['thresholdMin'] = args.seg_bkgd_thr_min
	if args.seg_bkgd_thr_max:
		options['thresholdMax'] = args.seg_bkgd_thr_max
	if args.seg_bkgd_thr_step:
		options['thresholdStep'] = args.seg_bkgd_thr_step

	if args.seg_seed_r:
		options['seedRadius'] = args.seg_seed_r
	if args.seg_seed_r_min:
		options['seedMin'] = args.seg_seed_r_min
	if args.seg_seed_r_max:
		options['seedMax'] = args.seg_seed_r_max
	if args.seg_seed_r_step:
		options['seedStep'] = args.seg_seed_r_step
			
	if args.seg_seed_thr:
		options['seedsThreshold'] = args.seg_seed_thr
	if args.seg_vol_min:
		options['volumeMin'] = args.seg_vol_min
	if args.seg_vol_max:
		options['volumeMax'] = args.seg_vol_max

	if args.one_shot:
		options['oneShot'] = True
	else:
		options['oneShot'] = False
		
	if args.seg_watershed:
		if str(args.seg_watershed).upper() == "TRUE":
			options['watershed'] = True
		else:
			options['watershed'] = False
	if args.exclude_edge_xy:
		if str(args.exclude_edge_xy).upper() == "TRUE":
			options['edgeXY'] = True
		else:
			options['edgeXY'] = False
	if args.exclude_edge_z:
		if str(args.exclude_edge_z).upper() == "TRUE":
			options['edgeZ'] = True
		else:
			options['edgeZ'] = False
else:
	options['inputFile'] = "sample.tif"
	options['outputDir'] = ""

if options['paramsOut'] == None:
	results = []
	image = IJ.openImage(options['inputFile'])
	
	if options['oneShot']:
		results.append(runSimulation(options, image))
	else:
		parameters = makeParameters(options)
		for index in range(0, len(parameters)):
			options.update(parameters[index])
			results.append(runSimulation(options, image))
	
	resultsTable = ResultsTable()
	resultsTable.showRowNumbers(False)

	for i in range(0, len(results)):
		if options['oneShot']:
			localBackground = options['localBackground']
			seedRadius = options['seedRadius']
			gaussXY = options['gaussXY']
			gaussZ = options['gaussZ']
		else:
			localBackground = parameters[i]['localBackground']
			seedRadius = parameters[i]['seedRadius']
			gaussXY = parameters[i]['gaussXY']
			gaussZ = parameters[i]['gaussZ']
		
		resultsTable.incrementCounter()
		resultsTable.addValue("Threshold", localBackground)
		resultsTable.addValue("Seed radius", seedRadius)
		resultsTable.addValue("GXY", gaussXY)
		resultsTable.addValue("GZ", gaussZ)
		resultsTable.addValue("TOTAL", results[i]['all'])
		resultsTable.addValue("0-250", results[i]['0'])
		resultsTable.addValue("251-500", results[i]['250'])
		resultsTable.addValue("501-750", results[i]['500'])
		resultsTable.addValue("751-1000", results[i]['750'])
		resultsTable.addValue("1001-1500", results[i]['1000'])
		resultsTable.addValue(">1501", results[i]['1500'])
		resultsTable.addValue("Skipped", results[i]['edge'])

	resultsTable.save(options['outputDir'] + options['outputFile'])

else:
	parametersTable = ResultsTable()
	parametersTable.showRowNumbers(False)
	parameters = makeParameters(options)
	
	for i in range(0, len(parameters)):
		parametersTable.incrementCounter()
		parametersTable.addValue("Threshold", parameters[i]['localBackground'])
		parametersTable.addValue("Seed radius", parameters[i]['seedRadius'])
		parametersTable.addValue("GXY", parameters[i]['gaussXY'])
		parametersTable.addValue("GZ", parameters[i]['gaussZ'])

	parametersTable.save(options['paramsOut'])
