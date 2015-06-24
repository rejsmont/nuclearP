options = getArgument();
segmented_start = indexOf(options, "segmented='") + 11;
segmented_end = indexOf(options, "'", segmented_start);
raw_start = indexOf(options, "raw='") + 5;
raw_end = indexOf(options, "'", raw_start);
segmented = substring(options, segmented_start, segmented_end);
raw = substring(options, raw_start, raw_end);

print("Using object map " + segmented + " to measure " + raw);

setBatchMode(true);
run("3D Manager");
selectWindow(segmented);
Ext.Manager3D_AddImage();
Ext.Manager3D_Count(objectNo);
selectWindow(raw);
run("Duplicate...", "title=" + raw + "_split duplicate");
getDimensions(width, height, channels, slices, frames)
run("Split Channels");

objectArray = newArray();
cxArray = newArray();
cyArray = newArray();
czArray = newArray();
volArray = newArray();
intArray = newArray();
meanArray = newArray();

for (k = 1; k <= channels; k++) {
	selectWindow("C" + k + "-" + raw + "_split");
	for (i = 0; i < objectNo; i++) {
		Ext.Manager3D_Quantif3D(i, "IntDen", int);
		Ext.Manager3D_Quantif3D(i, "Mean", mean);
		if (k == 1) {
			Ext.Manager3D_Centroid3D(i, cx, cy, cz);
			Ext.Manager3D_Measure3D(i, "Vol", vol);
			objectArray = Array.concat(objectArray, i + 1);
			cxArray = Array.concat(cxArray, cx);
			cyArray = Array.concat(cyArray, cy);
			czArray = Array.concat(czArray, cz);
			volArray = Array.concat(volArray, vol);
		}
		intArray = Array.concat(intArray, int);
		meanArray = Array.concat(meanArray, mean);
	}
	close();
}

Array.show(raw + "_objects", objectArray, cxArray, cyArray, czArray, volArray);

for (k = 1; k <= channels; k++) {
	intCArray = Array.slice(intArray, (k-1) * objectNo, k * objectNo);
	meanCArray = Array.slice(meanArray, (k-1) * objectNo, k * objectNo);
	Array.show(raw + "_measurements-C" + k, objectArray, intCArray, meanCArray);
	
}

Ext.Manager3D_Close();
setBatchMode(false);
