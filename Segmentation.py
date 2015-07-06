import ImageProcessing
reload(ImageProcessing)

from ImageProcessing import ImageProcessor
from ij import IJ, ImagePlus
from ij.plugin import Duplicator
from ij.process import ImageConverter
from mcib3d.image3d import ImageHandler
from mcib3d.image3d import Segment3DSpots
from mcib3d.image3d.processing import FastFilters3D

class Segmentator(ImageProcessor):

	### Class constructor
	def __init__(self, options, directory = ""):
		super(Segmentator, self).__init__(options, directory)
		self.seedRadius = options['seedRadius']
		self.seedsThreshold = options['seedsThreshold']
		self.localBackground = options['localBackground']
		self.watershed = options['watershed']
		self.volumeMin = options['volumeMin']
		self.volumeMax = options['volumeMax']

	### Perform segmentation
	def process(self, image, seeds = None):
		duplicator = Duplicator()
		spots = duplicator.run(image)
		IJ.setMinAndMax(spots, 0, 1)
		IJ.run(spots, "16-bit", "")
		spot3DImage = ImageHandler.wrap(spots)
		if seeds != None:
			seed3DImage = ImageHandler.wrap(seeds)
		else:
			seed3DImage = self.__computeSeeds(spots)
		
		algorithm = Segment3DSpots(spot3DImage, seed3DImage)
		algorithm.show = False
		algorithm.setSeedsThreshold(self.seedsThreshold)
		algorithm.setLocalThreshold(self.localBackground)
		algorithm.setWatershed(self.watershed)
		algorithm.setVolumeMin(self.volumeMin)
		algorithm.setVolumeMax(self.volumeMax)
		algorithm.setMethodLocal(Segment3DSpots.LOCAL_CONSTANT)
		algorithm.setMethodSeg(Segment3DSpots.SEG_MAX)
		algorithm.segmentAll()
		omap = ImagePlus("OM_" + spots.getTitle(), algorithm.getLabelImage().getImageStack())
		
		return omap

	### Compute watershed seeds
	def __computeSeeds(self, spots):
		seeds = FastFilters3D.filterIntImageStack(
			spots.getImageStack(), FastFilters3D.MAXLOCAL, self.seedRadius, self.seedRadius, self.seedRadius, 0, False)

		return ImageHandler.wrap(seeds)
		