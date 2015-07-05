import sys
import os

sys.path.append("/Users/u0078517/src/ImageProcessing/nuclearP")

### These imports are required in development environment
import Options
reload(Options)
import Decolvolution
reload(Decolvolution)
import Segment
reload(Segment)
import Measure3D
reload(Measure3D)

### Regular imports
from ij import IJ
from ij.io import DirectoryChooser, OpenDialog, FileSaver
from Options import getOptions, getDefaults
from Decolvolution import Decolvolution
from Segment import getProbabilityMap, segmentImage
from Measure3D import run3Dmeasurements, getResultsTable

### Get input dir / output dir / model file from user

inputDialog = DirectoryChooser("Please select a directory contaning your images")
outputDialog = DirectoryChooser("Please select a directory to save your results")
psfDialog = OpenDialog("Please select the psf image")
modelDialog = OpenDialog("Please select the model file")

inputDir = inputDialog.getDirectory()
outputDir = outputDialog.getDirectory()
psfFile = psfDialog.getPath()
options = getDefaults()
options['modelFile'] = modelDialog.getPath()

print "Input Directory: " + inputDir
print "Output Directory: " + outputDir
print "PSF file: " + psfFile
print "Model file: " + options['modelFile']

### Initiate segmentator
segmentator = None
deconvolutor = None

### Create required directories
if not os.path.exists(outputDir + "Deconvolved/"):
	os.makedirs(outputDir + "Deconvolved/")
if not os.path.exists(outputDir + "Maps/"):
	os.makedirs(outputDir + "Maps/")
if not os.path.exists(outputDir + "Segmented/"):
	os.makedirs(outputDir + "Segmented/")
if not os.path.exists(outputDir + "Results/"):
	os.makedirs(outputDir + "Results/")

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
	if deconvolutor = None:
		psf = IJ.openImage(psfFile)
		deconvolutor = Deconvolution(psf, options)
	deconvolvedImage = deconvolutor.process(inputImage)
	outputName =  "TM_" + "%f" % options['regparam'] + "_" + inputName
	saver = FileSaver(deconvolvedImage)
	saver.saveAsTiffStack(outputDir + "Deconvolved/" + outputName + ".tif")	
	print "Saved " + outputDir + "Deconvolved/" + outputName + ".tif"

	### Probability map calculation
	print "Calculating probability maps..."
	probabilityMaps = getProbabilityMap(deconvolvedImage, segmentator, options)
	for pmIndex, pmImage in enumerate(probabilityMaps):
		outputName =  "PM" + "%i" % pmIndex + "_" + inputName
		saver = FileSaver(pmImage)
		saver.saveAsTiffStack(outputDir + "Maps/" + outputName + ".tif")	
		print "Saved " + outputDir + "Maps/" + outputName + ".tif"

	### Blur nuclei probability map (1) to smoothen segmentation
	IJ.run(probabilityMaps[1], "Gaussian Blur 3D...", "x=2 y=2 z=1");

	### Segment image using nuclear probability map (1)
	print "Segmenting image..."
	segmentedImage = segmentImage(probabilityMaps[1], None, options)
	outputName =  "OM_" + inputName
	saver = FileSaver(segmentedImage)
	saver.saveAsTiffStack(outputDir + "Segmented/" + outputName + ".tif")
	print "Saved " + outputDir + "Segmented/" + outputName + ".tif"

	### Get object measurements
	print "Measuring objects..."
	measurements = run3Dmeasurements(segmentedImage, image)
	results = getResultsTable(measurements, image, options)
	outputName =  "OBJ_" + title
	results.save(outputDir + "Results/" + outputName + ".csv")
	print "Saved " + outputDir + "Results/" + outputName + ".csv"

	### This should be it!
	print "Image " + imageFile + " processed!"

