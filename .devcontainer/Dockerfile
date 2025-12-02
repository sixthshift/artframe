# Development container for Artframe
# Uses devcontainer base with Python and Node added via features
FROM mcr.microsoft.com/devcontainers/base:debian

ENV DEBIAN_FRONTEND=noninteractive

# Build dependencies for Python packages with C extensions
# Required for Pillow, cryptography, etc.
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
        build-essential \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        libffi-dev \
        libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
