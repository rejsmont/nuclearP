import ImageProcessing
reload(ImageProcessing)

from ImageProcessing import ImageProcessor
from deconv import Parameters
from deconv.algo import TikhonovMiller
from toolbox import Signal, ToolboxSignal
from java.awt import Rectangle
from jarray import zeros

class Deconvolutor(ImageProcessor):

	### Class constructor
	def __init__(self, psf, options, directory = ""):
		super(Deconvolutor, self).__init__(options, directory)
		self.psf = psf
		self.parameters = Parameters()
		self.parameters.useFFTW = True
		self.algorithm = TikhonovMiller()
		self.algorithm.K = options['iterations']
		self.algorithm.lambda = options['regparam']
		
	### Convert PSF image to signal array
	def __getH(self, y):
		h = Signal(self.psf)
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

	### Convert input image to signal array
	def __getY(self, image):
		roi = Rectangle(0,0, image.getWidth(), image.getHeight());
		slices = image.getStackSize();
		if slices != 1:
			y = Signal(image, roi, 0, slices)
		else:
			y = Signal(image, roi)

		return y

	### Correct slice order in deconvolved image
	def __correctStack(self, image):
		stack = image.getStack()
		temp = stack.getProcessor(1)
		stack.deleteSlice(1)
		stack.addSlice(temp)

		return image

	### Perform deconvolution
	def process(self, image):
		y = self.__getY(image)
		h = self.__getH(y)
		self.algorithm.process(y, h, None, self.parameters)
		outputName =  "TM_" + "%f" % self.algorithm.lambda + "_" + image.getTitle()
		result = y.get_image(outputName)
		
		return self.__correctStack(result)
		