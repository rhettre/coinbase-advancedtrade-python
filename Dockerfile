# Use the Amazon Linux 2023 image compatible with AWS Lambda
FROM amazonlinux:2023

# Install Python 3.9 and other necessary tools
RUN dnf install -y python3.9 python3.9-devel gcc zip && \
    dnf clean all

# Set up the work directory
WORKDIR /root

# Copy your application code and requirements.txt into the Docker image
COPY . .

# Create a virtual environment and install dependencies
RUN python3.9 -m venv /root/venv && \
    . /root/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install . && \
    deactivate

# Package everything into a ZIP file
CMD . /root/venv/bin/activate && \
    mkdir -p python/lib/python3.9/site-packages && \
    pip install \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.9 \
        --only-binary=:all: --upgrade \
        -r requirements.txt -t python/lib/python3.9/site-packages && \
    pip install . -t python/lib/python3.9/site-packages && \
    cd python/lib/python3.9/site-packages && \
    zip -r9 ../../../../layer.zip . && \
    cd ../../../../ && \
    deactivate