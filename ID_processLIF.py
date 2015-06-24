import sys
import os

from ij import IJ, ImagePlus, ImageStack, WindowManager
from ij.gui import GenericDialog
from ij.io import DirectoryChooser, OpenDialog, FileSaver
from ij.plugin import ChannelSplitter

from trainableSegmentation import WekaSegmentation


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

if not os.path.exists(outputDir + "Deconvolved/"):
    os.makedirs(outputDir + "Deconvolved/")

if not os.path.exists(outputDir + "Maps/"):
    os.makedirs(outputDir + "Maps/")

channel = -1
regparam = -1
iterations = -1
segmentator = None
psf = IJ.openImage(psfDir + "/" + psfFile)

for imageFile in os.listdir(inputDir):

	print "Opening " + inputDir + imageFile
	
	image = IJ.openImage(inputDir + imageFile)
	
	if channel == -1:
		channels = []
		for ch in range(1, image.getNChannels() + 1):
			channels.append("Channel " + "%i" % ch)
		dialog = GenericDialog("Select deconvolution parameters")
		dialog.addChoice("Channel to process", channels, None)
		dialog.addNumericField("Regularization parameter", 0.01, 2)
		dialog.addNumericField("Number of iterations", 1, 0)
		dialog.showDialog()
		if dialog.wasCanceled():
			sys.exit(1)
		channel = dialog.getNextChoiceIndex()
		regparam = dialog.getNextNumber()
		iterations = dialog.getNextNumber()
		print "Channel: " + "%i" % channel + " lambda: " + "%f" % regparam + " iter: " + "%i" % iterations

	print "Processing " + inputDir + imageFile

	inputName = "C" + "%i" % channel + "-" + imageFile
	outputName =  "TM_" + "%f" % regparam + "_" + inputName;

	splitter = ChannelSplitter()
	channelStack = splitter.getChannel(image, channel)
	rawImage = ImagePlus(inputName , channelStack)
	
	image.close()
	psf.show()
	rawImage.show()
	
	IJ.run("DeconvolutionLab ", 
		" namealgo='Tikhonov-Miller' lambda=" + "%f" % regparam + \
		" namepsf='" + psfFile + "' normalizepsf=true recenterpsf=true" + \
		" usefftw=true logpriority=1 nameoutput='" + outputName + "' k=" + "%i" % iterations)

	deconvolvedImage = WindowManager.getImage(outputName)
	while deconvolvedImage == None:
		deconvolvedImage = WindowManager.getImage(outputName)

	psf.hide()
	rawImage.close()
	deconvolvedImage.hide()

	deconvolvedStack = deconvolvedImage.getStack()
	tempSlice = deconvolvedStack.getProcessor(1)
	deconvolvedStack.deleteSlice(1)
	deconvolvedStack.addSlice(tempSlice)
	
	saver = FileSaver(deconvolvedImage)
	saver.saveAsTiffStack(outputDir + "Deconvolved/" + outputName + ".tif")
	print "Saved " + outputDir + "Deconvolved/" + outputName + ".tif"

	if segmentator == None:
		segmentator = WekaSegmentation(deconvolvedImage)
		segmentator.loadClassifier(modelFile)
	else:
		segmentator.loadNewImage(deconvolvedImage)

	segmentator.applyClassifier(True)
	pMap = segmentator.getClassifiedImage()
	pmStack = pMap.getStack()
	
	pmLabels = []
	pmStacks = []
	for slice in range(1, pmStack.getSize() + 1):
		pMap.setPosition(slice)
		label = pmStack.getSliceLabel(slice)
		if not label in pmLabels:
			pmLabels.append(label)
			pmcStack = ImageStack(pMap.getWidth(), pMap.getHeight())
			pmcStack.addSlice(pMap.getProcessor())
			pmStacks.append(pmcStack)
		else:
			index = pmLabels.index(label)
			pmStacks[index].addSlice(pMap.getProcessor())

	for pmcIndex, pmcStack in enumerate(pmStacks):
		pmImage = ImagePlus("PM" + "%i" % pmcIndex + "_" + inputName , pmcStack)
		saver = FileSaver(pmImage)
		saver.saveAsTiffStack(outputDir + "Maps/PM" + "%i" % pmcIndex + "_" + inputName + ".tif")
		print "Saved " + outputDir + "Maps/PM" + "%i" % pmcIndex + "_" + inputName + ".tif"

		if pmcIndex == 1:
			probabilityMap = pmImage		
		pmImage.close()

	pMap.close()
	deconvolvedImage.close()
	probabilityMap.setTitle("3D_segment_input")
	IJ.setMinAndMax(probabilityMap, 0, 1)
	IJ.run(probabilityMap, "16-bit", "")
	probabilityMap.show()

	seedRadius = 8
	
	IJ.run("3D Spot Segmentation", 
		" seeds_threshold=" + "%i" % 1 + " local_background=" + "%i" % 16383 + \
		" radius_0=" + "%i" % 3 + " radius_1=" + "%i" % 6 + " radius_2=" + "%i" % 9 + \
		" weigth=" + "%f" % 0.50 + " radius_max=" + "%i" % 10 + " sd_value=" + "%i" % 1 + \
		" local_threshold=[Local Mean] seg_spot=Classical watershed" + \
		" volume_min=" + "%i" % 50 + " volume_max=" + "%i" % 1000 + \
		" seeds=Automatic spots=" + probabilityMap.getTitle() + \
		" radius_for_seeds=" + "%i" % seedRadius + " output=[Label Image]")

	IJ.selectWindow("seg")
	segmentedImage = IJ.getImage()
	segmentedImage.setTitle("3D_segmented_" + inputName)

psf.close()
