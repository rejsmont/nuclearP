import os

from ij import IJ, ImagePlus, WindowManager
from ij.io import FileSaver
from ij.plugin import ChannelSplitter


def deconvolveImage(image, psf, options):	

	title = image.getTitle()
	title = title[:title.rfind('.')]
	inputName = "C" + "%i" % options['channel'] + "-" + title
	outputName =  "TM_" + "%f" % options['regparam'] + "_" + title

	splitter = ChannelSplitter()
	channelStack = splitter.getChannel(image, options['channel'])
	rawImage = ImagePlus(inputName , channelStack)
	
	psf.show()
	rawImage.show()

	deconvolveCommand = " namealgo='Tikhonov-Miller'" + \
		" lambda=" + "%f" % options['regparam'] + \
		" namepsf='" + psf.getTitle() + "'" + \
		" normalizepsf=true recenterpsf=true" + \
		" usefftw=true logpriority=1" + \
		" nameoutput='" + outputName + "'" + \
		" k=" + "%i" % options['iterations']
	IJ.run("DeconvolutionLab ", deconvolveCommand)

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

	if not os.path.exists(options['outputDir'] + "Deconvolved/"):
		os.makedirs(options['outputDir'] + "Deconvolved/")
	
	saver = FileSaver(deconvolvedImage)
	saver.saveAsTiffStack(options['outputDir'] + "Deconvolved/" + outputName + ".tif")
	
	print "Saved " + options['outputDir'] + "Deconvolved/" + outputName + ".tif"

	return deconvolvedImage
