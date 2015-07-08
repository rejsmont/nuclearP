import os
from ij.io import FileSaver

class ImageProcessor(object):

	### Class constructor
	def __init__(self, options, directory = ""):
		self.outputDir = options['outputDir']
		self.inputDir = options['inputDir']
		if directory != "":
			directory = directory + os.path.sep
			if not os.path.exists(self.outputDir + directory):
				os.makedirs(self.outputDir + directory)
		self.subDir = directory

	### Save results to outputDir
	def save(self, image, outputName):
		saver = FileSaver(image)
		saver.saveAsTiffStack(self.outputDir + self.subDir + outputName + ".tif")	
		print "Saved " + self.outputDir + self.subDir + outputName + ".tif"
