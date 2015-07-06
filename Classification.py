import ImageProcessing
reload(ImageProcessing)

from ImageProcessing import ImageProcessor
from ij import IJ, ImagePlus, ImageStack
from trainableSegmentation import WekaSegmentation

class Classificator(ImageProcessor):

	### Class constructor
	def __init__(self, options, directory = ""):
		super(Classificator, self).__init__(options, directory)
		self.algorithm = None
		self.modelFile = options['modelFile']

	### Perform classification
	def process(self, image):
		if self.algorithm == None:
			self.algorithm = WekaSegmentation(image)
			self.algorithm.loadClassifier(self.modelFile)
		else:
			self.algorithm.loadNewImage(image)
		self.algorithm.applyClassifier(True)
		pmaps = self.algorithm.getClassifiedImage()
		stacks = self.__splitMaps(pmaps)

		probabilityMaps = []
		for index, stack in enumerate(stacks):
			probabilityMaps.append(ImagePlus("PM" + "%i" % index + "_" + image.getTitle(), stack))
		
		return probabilityMaps

	### Split probability maps image into separate stacks for each class
	def __splitMaps(self, pmaps):
		pmstack = pmaps.getStack()
		labels = []
		stacks = []
		for pmslice in range(1, pmstack.getSize() + 1):
			pmaps.setPosition(pmslice)
			label = pmstack.getSliceLabel(pmslice)
			if not label in labels:
				labels.append(label)
				stack = ImageStack(pmaps.getWidth(), pmaps.getHeight())
				stack.addSlice(pmaps.getProcessor())
				stacks.append(stack)
			else:
				index = labels.index(label)
				stacks[index].addSlice(pmaps.getProcessor())

		return stacks
