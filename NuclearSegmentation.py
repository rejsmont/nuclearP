import sys
import os

### Import argparse to parse command-line arguments
import argparse

### These imports are required in development environment
import Options
reload(Options)
import Deconvolution
reload(Deconvolution)
import Classification
reload(Classification)
import Segmentation
reload(Segmentation)
import Analysis
reload(Analysis)

### Regular imports
from ij import IJ, ImagePlus
from ij.io import DirectoryChooser, OpenDialog, FileSaver
from ij.plugin import ChannelSplitter
from Options import getOptions, getDefaults
from Deconvolution import Deconvolutor
from Classification import Classificator
from Segmentation import Segmentator
from Analysis import Analyzer


options = getDefaults()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Nuclear Segmentation with Fiji")
	parser.add_argument('--input-dir')
	parser.add_argument('--input-file')
	parser.add_argument('--output-dir')
	parser.add_argument('--img-channel')
	parser.add_argument('--deconv-psf')
	parser.add_argument('--deconv-lambda')
	parser.add_argument('--deconv-k')
	parser.add_argument('--class-model')
	parser.add_argument('--gauss-xy')
	parser.add_argument('--gauss-z')
	parser.add_argument('--seg-bkgd-thr')
	parser.add_argument('--seg-seed-thr')
	parser.add_argument('--seg-seed-r')
	parser.add_argument('--seg-watershed')
	parser.add_argument('--seg-vol-min')
	parser.add_argument('--seg-vol-max')
	
	args = parser.parse_args()
	options['inputDir'] = args.input_dir
	options['inputFile'] = args.input_file
	options['outputDir'] = args.output_dir
	options['psfFile'] = args.deconv_psf
	options['modelFile'] = args.class_model
	if args.img_channel:
		options['channel'] = int(args.img_channel)
	if args.deconv_lambda:
		options['regparam'] = float(args.deconv_lambda)
	if args.deconv_k:
		options['iterations'] = int(args.deconv_k)
	if args.gauss_xy:
		options['gaussXY'] = float(args.gauss_xy)
	if args.gauss_z:
		options['gaussZ'] = float(args.gauss_z)
	if args.seg_bkgd_thr:
		options['localBackground'] = int(args.seg_bkgd_thr)
	if args.seg_seed_thr:
		options['seedsThreshold'] = int(args.seg_seed_thr)
	if args.seg_seed_r:
		options['seedRadius'] = int(args.seg_seed_r)
	if args.seg_vol_min:
		options['volumeMin'] = int(args.seg_vol_min)
	if args.seg_vol_max:
		options['volumeMax'] = int(args.seg_vol_max)
	if args.seg_watershed:
		if str(args.seg_watershed).upper() == "TRUE":
			options['watershed'] = True
		else:
			options['watershed'] = False
	
else:
	inputDialog = DirectoryChooser("Please select a directory contaning your images")
	outputDialog = DirectoryChooser("Please select a directory to save your results")
	psfDialog = OpenDialog("Please select the psf image")
	modelDialog = OpenDialog("Please select the model file")
	options['inputDir'] = inputDialog.getDirectory()
	options['outputDir'] = outputDialog.getDirectory()
	options['psfFile'] = psfDialog.getPath()
	options['modelFile'] = modelDialog.getPath()
	options.pop("channel", None)

print "Input Directory: " + options['inputDir']
print "Output Directory: " + options['outputDir']
print "PSF file: " + options['psfFile']
print "Model file: " + options['modelFile']


### Initiate worker objects
workers = {'deconvolutor': None, 'classificator': None, 'segmentator': None}

def process(imageFile, options, workers):
	### Open file for processing
	print "Opening " + imageFile
	image = IJ.openImage(imageFile)
	options = getOptions(options, image)
	title = image.getTitle()
	title = title[:title.rfind('.')]
	inputName = "C" + "%i" % options['channel'] + "-" + title

	### Extract channel used for segmentation
	splitter = ChannelSplitter()
	channelStack = splitter.getChannel(image, options['channel'])
	inputImage = ImagePlus("C" + "%i" % options['channel'] + "-" + image.getTitle() , channelStack)

	### Deconvolution
	print "Deconvolving image..."
	if workers['deconvolutor'] == None:
		psf = IJ.openImage(options['psfFile'])
		workers['deconvolutor'] = Deconvolutor(psf, options, "Deconvolved")
	deconvolvedImage = workers['deconvolutor'].process(inputImage)
	outputName =  "TM_" + "%f" % options['regparam'] + "_" + inputName
	workers['deconvolutor'].save(deconvolvedImage, outputName)

	### Classification
	print "Classifying image..."
	if workers['classificator'] == None:
		workers['classificator'] = Classificator(options, "Maps")
	probabilityMaps = workers['classificator'].process(deconvolvedImage)
	for pmIndex, pmImage in enumerate(probabilityMaps):
		outputName =  "PM" + "%i" % pmIndex + "_" + inputName
		workers['classificator'].save(pmImage, outputName)

	### Blur nuclei probability map (1) to smoothen segmentation
	IJ.run(probabilityMaps[1], "Gaussian Blur 3D...",
		" x=" + "%f" % options['gaussXY'] + \
		" y=" + "%f" % options['gaussXY'] + \
		" z=" + "%f" % options['gaussZ'])

	### Segment image using nuclear probability map (1)
	print "Segmenting image..."
	if workers['segmentator'] == None:
		workers['segmentator'] = Segmentator(options, "Segmented")
	segmentedImage = workers['segmentator'].process(probabilityMaps[1])
	outputName =  "OM_" + inputName
	workers['segmentator'].save(segmentedImage, outputName)

	### Get object measurements
	print "Measuring objects..."
	objects = workers['segmentator'].objects
	analyzer = Analyzer(options, objects, "Results")
	results = analyzer.getMeasurements(image)
	outputName =  "OBJ_" + title
	analyzer.save(results, outputName)

	### This should be it!
	print "Image " + imageFile + " processed!"
	
	return objects


if options['inputDir']:
	for imageFile in os.listdir(options['inputDir']):
		process(options['inputDir'] + imageFile, options, workers)
elif options['inputFile']:
	process(options['inputFile'], options, workers)
