import Deconvolution
reload(Deconvolution)

### Regular imports
from ij import IJ, ImagePlus
from ij.plugin import ChannelSplitter
from Deconvolution import Deconvolution

options = {}
options['channel'] = 0
options['regparam'] = 0.01
options['iterations'] = 50
image = IJ.openImage("/Users/u0078517/Desktop/Samples/E2C-disc-1-sample.tif")
psf = IJ.openImage("/Users/u0078517/Desktop/Parameters/PSF-Venus-test.tif")

image.show()
psf.show()

splitter = ChannelSplitter()
channelStack = splitter.getChannel(image, options['channel'])
rawImage = ImagePlus("C" + "%i" % options['channel'] + "-" + image.getTitle() , channelStack)

print "Starting deconvolution"
deconvolutor = Deconvolution(psf, options)
deconvolvedImage = deconvolutor.process(rawImage)

print "Finished"
deconvolvedImage.show()
