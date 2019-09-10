# Creates docker container that runs FSL pipelines
#

# Use prepared fsl-base:6.0.1 based on ubuntu:xenial
FROM flywheel/fsl-base:6.0.1

MAINTAINER Flywheel <support@flywheel.io>

# Configure FSL environment
ENV FSLDIR=/usr/share/fsl/6.0
ENV FSL_DIR="${FSLDIR}"
ENV PATH=/usr/lib/fsl/6.0:$PATH
ENV FSLMULTIFILEQUIT=TRUE
ENV POSSUMDIR=/usr/share/fsl/6.0
ENV LD_LIBRARY_PATH=/usr/lib/fsl/6.0:$LD_LIBRARY_PATH
ENV FSLTCLSH=/usr/bin/tclsh
ENV FSLWISH=/usr/bin/wish
ENV FSLOUTPUTTYPE=NIFTI_GZ

# Save docker environ
RUN python -c 'import os, json; f = open("/tmp/gear_environ.json", "w"); json.dump(dict(os.environ), f)' && \
pip3 install flywheel-sdk
#############################################

# Install additional library
RUN apt install -y tree

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
WORKDIR ${FLYWHEEL}

# Copy executable/manifest to Gear
COPY run.py ${FLYWHEEL}/run.py
COPY manifest.json ${FLYWHEEL}/manifest.json
COPY utils ${FLYWHEEL}/utils

# Configure entrypoint
RUN chmod a+x /flywheel/v0/run.py
ENTRYPOINT ["/flywheel/v0/run.py"]