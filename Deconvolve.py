from ij import IJ, ImagePlus, WindowManager
from ij.plugin import ChannelSplitter


def deconvolveImage(image, psf, options):	

	splitter = ChannelSplitter()
	channelStack = splitter.getChannel(image, options['channel'])
	rawImage = ImagePlus("C" + "%i" % options['channel'] + "-" + image.getTitle() , channelStack)
	
	psf.show()
	rawImage.show()

	outputName =  "TM_" + "%f" % options['regparam'] + "_" + image.getTitle()

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

	return deconvolvedImage
