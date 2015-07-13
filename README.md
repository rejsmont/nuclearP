# nuclearP
This project aims to create a comprehensive set of ImageJ macros for nuclear segmentation
and fluorescence intensity measurements in Drosophila eye discs. It uses Deconvolution Lab for
Tikhonov-Mueller deconvolution, WEKA for machine learning-based probability map calculation and
3D ImageJ Suite for final segmentation and 3D object management.

The macros are implemented in Jython and use Java APIs of plugins.

To run the script from console, follow this example:
```
fiji --headless ./NuclearSegmentation.py --input-dir=./examples/input/ --class-model=./examples/nuclei-test.model --deconv-psf=./examples/psf-test.tif --output-dir=../output
```
