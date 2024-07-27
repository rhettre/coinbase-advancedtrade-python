# Use the Amazon Linux 2023 image compatible with AWS Lambda
FROM public.ecr.aws/lambda/python:3.9

# Set up the work directory
WORKDIR /var/task

# Install necessary build tools and Rust
RUN yum install -y zip gcc python3-devel libffi-devel && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    echo 'source $HOME/.cargo/env' >> $HOME/.bashrc && \
    source $HOME/.cargo/env

# Copy your application code and requirements.txt into the Docker image
COPY . .

# Install dependencies and create the layer
RUN source $HOME/.cargo/env && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install . && \
    mkdir -p /tmp/python && \
    pip install \
        --platform manylinux2014_$(uname -m) \
        --implementation cp \
        --python-version 3.9 \
        --only-binary=:all: --upgrade \
        -r requirements.txt -t /tmp/python && \
    pip install cffi --no-binary cffi -t /tmp/python && \
    pip install cryptography --no-binary cryptography -t /tmp/python && \
    pip install . -t /tmp/python && \
    cd /tmp/python && \
    find . -type d -name "__pycache__" -exec rm -rf {} + && \
    zip -r9 /tmp/layer.zip . && \
    cd /var/task

# Copy the layer.zip to a known location
CMD cp /tmp/layer.zip /asset-output/layer.zip