import os

from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from ij.plugin import Duplicator
from trainableSegmentation import WekaSegmentation


def getProbabilityMap(image, segmentator, options):		

	if segmentator == None:
		segmentator = WekaSegmentation(image)
		segmentator.loadClassifier(options['modelFile'])
	else:
		segmentator.loadNewImage(image)

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

	probabilityMaps = []
	for pmcIndex, pmcStack in enumerate(pmStacks):
		probabilityMaps.append(ImagePlus("PM" + "%i" % pmcIndex + "_" + image.getTitle(), pmcStack))
	pMap.close()

	return probabilityMaps


def segmentImage(probabilityMap, seedImage, options):

	if probabilityMap != None:
		duplicator = Duplicator()
		image = duplicator.run(probabilityMap)
		image.setTitle("3D_segment_input")
		IJ.setMinAndMax(image, 0, 1)
		IJ.run(image, "16-bit", "")
		image.show()
	else:
		image = None

	if seedImage != None:
		duplicator = Duplicator()
		seed = duplicator.run(seedImage)
		seed.setTitle("3D_segment_seed")
		seed.show()
	else:
		seed = None

	segmentCommand = " seeds_threshold=" + "%i" % options['seedsThreshold'] + \
		" local_background=" + "%i" % options['localBackground'] + \
		" radius_0=" + "%i" % options['radius_0'] + \
		" radius_1=" + "%i" % options['radius_1'] + \
		" radius_2=" + "%i" % options['radius_2'] + \
		" weigth=" + "%f" % options['weigth'] + \
		" radius_max=" + "%i" % options['radiusMax'] + \
		" sd_value=" + "%i" % options['sdValue'] + \
		" local_threshold=[" + options['localThreshold'] + "]" + \
		" seg_spot=[" + options['segSpot'] + "]" + \
		( " watershed" if options['watershed'] else "" ) + \
		" volume_min=" + "%i" % options['volumeMin'] + \
		" volume_max=" + "%i" % options['volumeMax'] + \
		" seeds=" + ( "Automatic" if seed == None else seed.getTitle() ) + \
		" spots=" + ( "Automatic" if image == None else image.getTitle() ) + \
		" radius_for_seeds=" + "%i" % options['seedRadius'] + \
		" output=[Label Image]"
	IJ.run("3D Spot Segmentation", segmentCommand)

	IJ.selectWindow("seg")
	segmentedImage = IJ.getImage()
	segmentedImage.setTitle("OM_" + probabilityMap.getTitle())
	segmentedImage.hide()

	if image != None:
		image.changes = False
		image.close()
	if seed != None:
		image.seed = False
		seed.close()

	return segmentedImage
