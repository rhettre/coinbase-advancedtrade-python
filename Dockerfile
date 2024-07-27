# Use the Amazon Linux 2023 image compatible with AWS Lambda
FROM public.ecr.aws/lambda/python:3.9

# Set up the work directory
WORKDIR /var/task

# Copy your application code and requirements.txt into the Docker image
COPY . .

# Install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install .

# Package everything into a ZIP file
CMD mkdir -p python/lib/python3.9/site-packages && \
    pip install \
        --platform manylinux2014_$(uname -m) \
        --implementation cp \
        --python-version 3.9 \
        --only-binary=:all: --upgrade \
        -r requirements.txt -t python/lib/python3.9/site-packages && \
    pip install . -t python/lib/python3.9/site-packages && \
    cd python/lib/python3.9/site-packages && \
    zip -r9 /asset-output/layer.zip . && \
    cd /var/task