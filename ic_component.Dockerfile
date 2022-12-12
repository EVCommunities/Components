# Copyright 2022 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ali Mehraj <ali.mehraj@tuni.fi>

# define the version of Python here
FROM python:3.7.9
LABEL org.opencontainers.image.source https://github.com/simcesplatform/user-component
LABEL org.opencontainers.image.description "Docker image for the ic-component for the SimCES platform."

# create the required directories inside the Docker image
RUN mkdir -p /ic_component
RUN mkdir -p /init
RUN mkdir -p /logs
RUN mkdir -p /simulation-tools
RUN mkdir -p /messages

# install the python libraries inside the Docker image
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

# copy the required directories with their content to the Docker image
COPY ic_component/ /ic_component/
COPY messages/ /messages/
COPY init/ /init/
COPY simulation-tools/ /simulation-tools/


# set the working directory inside the Docker image
WORKDIR /

# start command that is run when a Docker container using the image is started

CMD [ "python3", "-u", "-m", "ic_component.ICComponent" ]