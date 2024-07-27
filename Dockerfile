# Use the Amazon Linux 2023 image compatible with AWS Lambda
FROM amazonlinux:2023

# Install Python 3.9 and other necessary tools
RUN dnf install -y python3.9 python3.9-pip zip && \
    dnf clean all

# Set up the work directory
WORKDIR /root

# Copy your application code and requirements.txt into the Docker image
COPY . .

# Install dependencies directly into the Lambda-compatible directory structure
RUN mkdir -p python/lib/python3.9/site-packages && \
    python3.9 -m pip install \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.9 \
        --only-binary=:all: --upgrade \
        -r requirements.txt -t python/lib/python3.9/site-packages && \
    python3.9 -m pip install . -t python/lib/python3.9/site-packages

# Package everything into a ZIP file
CMD cd python && \
    zip -r ../layer.zip . && \
    cd ..