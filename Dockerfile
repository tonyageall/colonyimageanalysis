from 812206152185.dkr.ecr.us-west-2.amazonaws.com/latch-base:fe0b-main

WORKDIR /tmp/docker-build/work/

COPY . /tmp/docker-build/work/


shell [ \
    "/usr/bin/env", "bash", \
    "-o", "errexit", \
    "-o", "pipefail", \
    "-o", "nounset", \
    "-o", "verbose", \
    "-o", "errtrace", \
    "-O", "inherit_errexit", \
    "-O", "shift_verbose", \
    "-c" \
]
env TZ='Etc/UTC'
env LANG='en_US.UTF-8'


arg DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential

# install Automation-Consolidation
RUN pip install -r requirements.txt


# Latch SDK
# DO NOT REMOVE
run pip install latch==2.47.9
run mkdir /opt/latch


# Copy workflow data (use .dockerignore to skip files)
copy . .latch/* /root/


# Latch workflow registration metadata
# DO NOT CHANGE
arg tag
# DO NOT CHANGE
env FLYTE_INTERNAL_IMAGE $tag


workdir /root