# Use the Amazon Linux 2023 image compatible with AWS Lambda
FROM public.ecr.aws/lambda/python:3.9

# Set up the work directory
WORKDIR /var/task

# Copy your application code and requirements.txt into the Docker image
COPY . .

# Install dependencies and create the layer
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install . && \
    mkdir -p python/lib/python3.9/site-packages && \
    pip install \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.9 \
        --only-binary=:all: --upgrade \
        -r requirements.txt -t python/lib/python3.9/site-packages && \
    pip install . -t python/lib/python3.9/site-packages && \
    cd python/lib/python3.9/site-packages && \
    zip -r9 /tmp/layer.zip . && \
    cd /var/task

# Copy the layer.zip to a known location
CMD cp /tmp/layer.zip /asset-output/layer.zip