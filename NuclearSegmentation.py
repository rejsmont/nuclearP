import sys
import os

sys.path.append("/Users/u0078517/src/ImageProcessing/nuclearP")

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
from Segment import getProbabilityMap, segmentImage
from Measure3D import run3Dmeasurements, getResultsTable

### Get input dir / output dir / model file from user

#inputDialog = DirectoryChooser("Please select a directory contaning your images")
#outputDialog = DirectoryChooser("Please select a directory to save your results")
#psfDialog = OpenDialog("Please select the psf image")
#modelDialog = OpenDialog("Please select the model file")
#inputDir = inputDialog.getDirectory()
#outputDir = outputDialog.getDirectory()
#psfFile = psfDialog.getPath()
options = getDefaults()
#options['modelFile'] = modelDialog.getPath()


### Hard-coded options for testing
inputDir = "/Users/u0078517/Desktop/Samples/"
outputDir = "/Users/u0078517/Desktop/Output/"
psfFile = "/Users/u0078517/Desktop/Parameters/PSF-Venus-test.tif"
modelFile = "/Users/u0078517/Desktop/Parameters/classifier.model"
options['modelFile'] = modelFile
options['channel'] = 0
options['regparam'] = 0.01
options['iterations'] = 50

options['inputDir'] = inputDir
options['outputDir'] = outputDir

print "Input Directory: " + options['inputDir']
print "Output Directory: " + options['outputDir']
print "PSF file: " + psfFile
print "Model file: " + options['modelFile']

### Initiate segmentator
deconvolutor = None
classificator = None
segmentator = None

### Loop through input images
for imageFile in os.listdir(inputDir):

	### Open file for processing
	print "Opening " + inputDir + imageFile
	image = IJ.openImage(inputDir + imageFile)
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
	if deconvolutor == None:
		psf = IJ.openImage(psfFile)
		deconvolutor = Deconvolutor(psf, options, "Deconvolved")
	deconvolvedImage = deconvolutor.process(inputImage)
	outputName =  "TM_" + "%f" % options['regparam'] + "_" + inputName
	deconvolutor.save(deconvolvedImage, outputName)

	### Classification
	print "Classifying image..."
	if classificator == None:
		classificator = Classificator(options, "Maps")
	probabilityMaps = classificator.process(deconvolvedImage)
	for pmIndex, pmImage in enumerate(probabilityMaps):
		outputName =  "PM" + "%i" % pmIndex + "_" + inputName
		classificator.save(pmImage, outputName)

	### Blur nuclei probability map (1) to smoothen segmentation
	IJ.run(probabilityMaps[1], "Gaussian Blur 3D...", "x=2 y=2 z=1");

	### Segment image using nuclear probability map (1)
	print "Segmenting image..."
	if segmentator == None:
		segmentator = Segmentator(options, "Segmented")
	segmentedImage = segmentator.process(probabilityMaps[1])
	outputName =  "OM_" + inputName
	segmentator.save(segmentedImage, outputName)

	### Get object measurements
	print "Measuring objects..."
	analyzer = Analyzer(options, segmentator.objects, "Results")
	results = analyzer.getMeasurements(image)
	outputName =  "OBJ_" + title
	analyzer.save(results, outputName)

	### This should be it!
	print "Image " + imageFile + " processed!"

