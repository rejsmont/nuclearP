from ij import IJ, ImagePlus, WindowManager
from ij.plugin import ChannelSplitter
from deconv import Parameters
from deconv.algo import TikhonovMiller
from toolbox import Signal, ToolboxSignal
from java.awt import Rectangle
from jarray import zeros

def deconvolveImage(image, psf, options):	

	splitter = ChannelSplitter()
	channelStack = splitter.getChannel(image, options['channel'])
	rawImage = ImagePlus("C" + "%i" % options['channel'] + "-" + image.getTitle() , channelStack)
	
	#psf.show()
	#rawImage.show()

	outputName =  "TM_" + "%f" % options['regparam'] + "_" + image.getTitle()

	# Set deconvolution parameters and initialize the algorithm
	parameters = Parameters()
	parameters.useFFTW = True
	
	deconvoluter = TikhonovMiller()
	deconvoluter.K = options['iterations']
	deconvoluter.lambda = options['regparam']

	# Convert input image to Signal matrix
	roi = Rectangle(0,0, image.getWidth(), image.getHeight());
	slices = image.getStackSize();
	if slices != 1:
		y = Signal(image, roi, 0, slices)
	else:
		y = Signal(image, roi)

	# Convert PSF to Signal matrix
	h = Signal(psf)
	# Normalize PSF
	ToolboxSignal.multiplyConstant(h, 1/ToolboxSignal.sum(h))
	# Flip PSF quadrants
	shift = zeros(h.D, "i")
	for d in range(0, h.D):
		shift[d] = h.N[d] / 2
	ToolboxSignal.fftShift(h, shift) 
	# Resize PSF
	if not ToolboxSignal.checkCompatibility(y, h):
		ToolboxSignal.resizePSF(y.N, h)

	deconvoluter.process(y, h, None, parameters)
	deconvolvedImage = y.get_image(outputName)
	
	#deconvolveCommand = " namealgo='Tikhonov-Miller'" + \
	#	" lambda=" + "%f" % options['regparam'] + \
	#	" namepsf='" + psf.getTitle() + "'" + \
	#	" normalizepsf=true recenterpsf=true" + \
	#	" usefftw=true logpriority=1" + \
	#	" nameoutput='" + outputName + "'" + \
	#	" k=" + "%i" % options['iterations']
	#IJ.run("DeconvolutionLab ", deconvolveCommand)

	#deconvolvedImage = WindowManager.getImage(outputName)
	#while deconvolvedImage == None:
	#	deconvolvedImage = WindowManager.getImage(outputName)

	#psf.hide()
	#rawImage.close()
	#deconvolvedImage.hide()

	deconvolvedStack = deconvolvedImage.getStack()
	tempSlice = deconvolvedStack.getProcessor(1)
	deconvolvedStack.deleteSlice(1)
	deconvolvedStack.addSlice(tempSlice)

	return deconvolvedImage

def preparePSF(psf):
	# Convert PSF to Signal matrix
	h = Signal(psf)
	# Normalize PSF
	ToolboxSignal.multiplyConstant(h, 1/ToolboxSignal.sum(h))
	# Flip PSF quadrants
	shift = zeros(h.D, "i")
	for d in range(0, h.D):
		shift[d] = h.N[d] / 2
	ToolboxSignal.fftShift(h, shift) 
	# Resize PSF
	if not ToolboxSignal.checkCompatibility(y, h):
		ToolboxSignal.resizePSF(y.N, h)

	return h