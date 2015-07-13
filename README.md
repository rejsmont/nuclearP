# nuclearP
This project aims to create a comprehensive set of ImageJ macros for nuclear segmentation
and fluorescence intensity measurements in Drosophila eye discs. It uses Deconvolution Lab for
Tikhonov-Mueller deconvolution, WEKA for machine learning-based probability map calculation and
3D ImageJ Suite for final segmentation and 3D object management.

The macros are implemented in Jython and use Java APIs of plugins.

To run the segmentation script from console, follow this example:
```
fiji --headless ./NuclearSegmentation.py \
    --input-dir=./examples/input/ \
    --class-model=./examples/nuclei-test.model \
    --deconv-psf=./examples/psf-test.tif \
    --output-dir=../output
```

To generate parameters file for optimizer:
```
fiji --headless ./SegmentationOptimizer.py \
    --params-out='parameters.csv' \
    --gauss-xy-min=0 \
    --gauss-xy-max=5.2 \
    --gauss-xy-step=0.2 \
    --gauss-z-min=0 \
    --gauss-z-steps=5 \
    --seg-bkgd-thr-min=4096 \
    --seg-bkgd-thr-max=36864 \
    --seg-bkgd-thr-step=4096 \
    --seg-seed-r-min=2 \
    --seg-seed-r-max=13 \
    --seg-seed-r-step=2
```

To run simulation for single paramater set:
```
fiji --headless ./SegmentationOptimizer.py \
    --one-shot=true \
    --gauss-xy=2 \
    --gauss-z=1 \
    --seg-bkgd-thr=12288 \
    --seg-seed-r=2 \
    --input-file=./examples/PM1_C0-sample.tif \
    --output-dir=../output/ \
    --output-file=simulation-2-1-12288-2.csv
```

To run simulations whole paramater array:
```
fiji --headless ./SegmentationOptimizer.py \
    --gauss-xy-min=0 \
    --gauss-xy-max=3 \
    --gauss-xy-step=1 \
    --gauss-z-min=0 \
    --gauss-z-steps=1 \
    --seg-bkgd-thr-min=12288 \
    --seg-bkgd-thr-max=16384 \
    --seg-bkgd-thr-step=4096 \
    --seg-seed-r-min=2 \
    --seg-seed-r-max=4 \
    --seg-seed-r-step=2 \
    --input-file=./examples/PM1_C0-sample.tif \
    --output-dir=../output/ \
    --output-file=simulation-results.csv
```
