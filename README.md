# fsl-anat
A Flywheel gear for running FSL's Processing Script: fsl_anat

Build context for a [Flywheel Gear](https://github.com/flywheel-io/gears/tree/master/spec) to execute FSL's [fsl_anat](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/fsl_anat).

This Gear performs the fsl_anat (Anatomical Processing Script) general general pipeline for processing anatomical images (e.g. T1-weighted scans).

Most of the pipeline involves standard use of FSL tools, but the bias-field correction has been substantially improved, especially for strong bias-fields typical of multi-coil arrays and high-field scanners.

The stages in the pipeline (in order) are:

reorient the images to the standard (MNI) orientation [fslreorient2std]

automatically crop the image [robustfov]

bias-field correction (RF/B1-inhomogeneity-correction) [FAST]

registration to standard space (linear and non-linear) [FLIRT and FNIRT]

brain-extraction [FNIRT-based or BET]

tissue-type segmentation [FAST]

subcortical structure segmentation [FIRST]

The overall run-time is heavily dependent on the resolution of the image but anything between 30 and 90 minutes would be typical.