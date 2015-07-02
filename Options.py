import sys

from ij.gui import GenericDialog
from ij.io import DirectoryChooser, OpenDialog

def getOptions(options, image):
	if 'channel' not in options:
		channels = []
		for ch in range(1, image.getNChannels() + 1):
			channels.append("Channel " + "%i" % ch)
		dialog = GenericDialog("Select deconvolution parameters")
		dialog.addChoice("Channel to process", channels, None)
		dialog.addNumericField("Regularization parameter", 0.01, 2)
		dialog.addNumericField("Number of iterations", 50, 0)
		dialog.showDialog()
		if dialog.wasCanceled():
			sys.exit(1)	
		options['channel'] = dialog.getNextChoiceIndex()
		options['regparam'] = dialog.getNextNumber()
		options['iterations'] = dialog.getNextNumber()
	
	print "Channel: " + "%i" % options['channel'] + " lambda: " + "%f" % options['regparam'] + " iter: " + "%i" % options['iterations']
	
	return options

def getDefaults():
	options = {}

##### 3D Segmentation parameters #####
	# This setting selects a method used to determine voxels belong to background
	# Three options are possible: 'Constant', 'Local mean', and 'Gaussian fit'
	options['localThreshold'] = 'Constant'
	# Set this option of 'Constant' is used:
	options['localBackground'] = 12287
	# Set these options if 'Local mean' is used:
	options['radius_0'] = 3
	options['radius_1'] = 6
	options['radius_2'] = 9
	options['weigth'] = 0.50
	# Set these options if 'Gaussian fit' is used:
	options['radiusMax'] = 10
	options['sdValue'] = 1
	# This setting selects the voxel clustering method
	# Three options are possible: 'Classical', 'Maximum', 'Block'
	options['segSpot'] = 'Maximum'
	# Do you want to run 3d watershed on the segmented image?
	options['watershed'] = True
	# For wathershed set the following:
	options['seedsThreshold'] = 127
	options['seedRadius'] = 2
	# Discard objects with volumes smaller than 'volumeMin'
	# or larger than 'volumeMax'
	options['volumeMin'] = 50
	options['volumeMax'] = 10000


	# That should be it!
	return options
