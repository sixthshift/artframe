# Development-only container for Artframe
# Production runs directly on Raspberry Pi
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install only build dependencies needed for Python packages
# These are required for compiling Python packages with C extensions
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
        # C compiler and build tools
        build-essential \
        # Image processing libraries for Pillow
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        # Cryptography libraries
        libffi-dev \
        libssl-dev \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install uv - fast Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Python environment configuration
ENV PYTHONPATH=/workspace/src
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV UV_SYSTEM_PYTHON=1
ENV DEBIAN_FRONTEND=dialog

WORKDIR /workspace

CMD ["/bin/bash"]