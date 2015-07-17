import ImageProcessing
reload(ImageProcessing)

from ImageProcessing import ImageProcessor
from ij import IJ, ImagePlus
from ij.measure import ResultsTable
from ij.plugin import ChannelSplitter, Duplicator
from java.util import ArrayList
from mcib3d.image3d import ImageHandler
from mcib3d.image3d import ImageInt
from mcib3d.image3d import Segment3DSpots
from mcib3d.image3d.processing import FastFilters3D
from mcib3d.geom import Voxel3D
from mcib3d.geom import Object3DVoxels
from mcib3d.geom import Objects3DPopulation

class Analyzer(ImageProcessor):

	### Class constructor
	def __init__(self, options, objects = None, directory = ""):
		super(Analyzer, self).__init__(options, directory)
		if (objects):
			self.objects = None
			self.loadObjects(objects)
		else:
			self.objects = Objects3DPopulation()
		
	### Load objects from list or label image
	def loadObjects(self, objects):
		self.objects = Objects3DPopulation()
		self.addObjects(objects)

	### Add objects from list or label image
	def addObjects(self, objects):
		if isinstance(objects, ImagePlus):
			#labelImage = ImageInt.wrap(objects)
			voxels = self.__readVoxels(objects)
			self.__addVoxels(voxels, objects)
		else:
			for objectV in objects:
				self.objects.addObject(objectV) 

	### Read voxels from label image
	def __readVoxels(self, imagePlus):
		image = ImageInt.wrap(imagePlus)
		minX = 0
		maxX = image.sizeX
		minY = 0
		maxY = image.sizeY
		minZ = 0
		maxZ = image.sizeZ
		minV = int(image.getMinAboveValue(0))
		maxV = int(image.getMax())
		voxels = []
		for i in range(0, maxV - minV + 1):
			vlist = ArrayList()
			voxels.append(vlist)
		for k in range(minZ, maxZ):
			for j in range(minY, maxY):
				for i in range(minX, maxX):
					pixel = image.getPixel(i, j, k)
					if pixel > 0:
						voxel = Voxel3D(i, j, k, pixel)
						oid = int(pixel) - minV
						voxels[oid].add(voxel)
		objectVoxels = []
		for i in range(0, maxV - minV + 1):
			if voxels[i]:
				objectVoxels.append(voxels[i])

		return objectVoxels

	### Create objects from label image voxels
	def __addVoxels(self, objectVoxels, imagePlus):
		image = ImageInt.wrap(imagePlus)
		calibration = image.getCalibration();
		for voxels in objectVoxels:
			if voxels:
				objectV = Object3DVoxels(voxels)
				objectV.setCalibration(calibration)
				objectV.setLabelImage(image)
				objectV.computeContours()
				objectV.setLabelImage(None)
				self.objects.addObject(objectV)

	### Return 3D measurements
	def getMeasurements(self, image):
		imageChannels = []
		splitter = ChannelSplitter()
		for channel in range (0, image.getNChannels()):
			channelStack = splitter.getChannel(image, channel + 1)
			imageChannels.append(ImageHandler.wrap(channelStack))
	
		results = ResultsTable()
		results.showRowNumbers(False)
		
		for index, objectV in enumerate(self.objects.getObjectsList()):
			results.incrementCounter()
			results.addValue("Particle", index + 1)
			results.addValue("cx", objectV.getCenterX())
			results.addValue("cy", objectV.getCenterY())
			results.addValue("cz", objectV.getCenterZ())
			results.addValue("Volume", objectV.getVolumePixels())

			for channel, channelImage in enumerate(imageChannels):
				results.addValue("Integral " + "%i" % channel,  objectV.getIntegratedDensity(channelImage))
				results.addValue("Mean " + "%i" % channel, objectV.getPixMeanValue(channelImage))

		return results
		
	### Save results to outputDir
	def save(self, results, outputName):
		results.save(self.outputDir + self.subDir + outputName + ".csv")
		print "Saved " + self.outputDir + self.subDir + outputName + ".csv"
