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
	
	return options

def getDefaults():
	options = {}

	### Default options for Deconvolution
	options['channel'] = 0
	options['regparam'] = 0.01
	options['iterations'] = 50

	### Blur parameters - 0 for no blur ###
	options['gaussXY'] = 2
	options['gaussZ'] = 0

	### 3D Segmentation parameters ###
	options['localBackground'] = 12287
	options['seedsThreshold'] = 127
	options['volumeMin'] = 50
	options['volumeMax'] = 10000
	options['seedRadius'] = 2
	options['watershed'] = True
	
	return options
