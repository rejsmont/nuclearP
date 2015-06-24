from ij import IJ, WindowManager
from ij.measure import ResultsTable
from ij.plugin import Macro_Runner

def run3Dmeasurements(segmentedImage, rawImage):
	segmented = segmentedImage.getTitle()
	raw = rawImage.getTitle()
	segmentedImage.show()
	rawImage.show()
	runner = Macro_Runner()
	runner.runMacroFile("/Users/u0078517/src/ImageProcessing/nuclearP/ProcessObjects.ijm",
		"segmented='" + segmented + "' raw='" + raw + "'")
	segmentedImage.hide()
	rawImage.hide()
	
	return get3Dmeasurements(raw + "_objects", raw + "_measurements", rawImage.getNChannels())

def get3Dmeasurements(objectsTable, measurementTable, channels):

	IJ.renameResults(objectsTable, "Results")
	results_table =  ResultsTable.getResultsTable()

	objects = []

	for index in range(0, results_table.getCounter()):
		cx = results_table.getValue("cxArray", index)
		cy = results_table.getValue("cyArray", index)
		cz = results_table.getValue("czArray", index)
		vol = results_table.getValue("volArray", index)

		vals = {}
		vals['cx'] = cx
		vals['cy'] = cy
		vals['cz'] = cz
		vals['vol'] = vol
		vals['measurements'] = []

		objects.append(vals)

	results_table.getResultsWindow().close(False)

	for channel in range(1, channels+1):
		IJ.renameResults(measurementTable + "-C" + "%i" % channel, "Results")
		results_table =  ResultsTable.getResultsTable()

		for index in range(0, results_table.getCounter()):
			integral = results_table.getValue("intCArray", index)
			mean = results_table.getValue("meanCArray", index)

			vals = {}
			vals['int'] = integral
			vals['mean'] = mean

			objects[index]['measurements'].append(vals)

		results_table.getResultsWindow().close(False)

	return objects
