# Use the Amazon Linux 2023 image compatible with AWS Lambda
FROM public.ecr.aws/lambda/python:3.9

# Set up the work directory
WORKDIR /var/task

# Install necessary build tools, Rust, and OpenSSL
RUN yum install -y zip gcc python3-devel libffi-devel tar gzip make && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    echo 'source $HOME/.cargo/env' >> $HOME/.bashrc && \
    source $HOME/.cargo/env && \
    yum install -y wget && \
    wget https://www.openssl.org/source/openssl-1.1.1k.tar.gz && \
    tar -xzvf openssl-1.1.1k.tar.gz && \
    cd openssl-1.1.1k && \
    ./config --prefix=/usr/local/ssl --openssldir=/usr/local/ssl shared zlib && \
    make && make install && \
    echo "/usr/local/ssl/lib" > /etc/ld.so.conf.d/openssl-1.1.1k.conf && \
    ldconfig && \
    cd .. && rm -rf openssl-1.1.1k*

# Set OpenSSL environment variables
ENV LDFLAGS="-L/usr/local/ssl/lib"
ENV CPPFLAGS="-I/usr/local/ssl/include"
ENV LD_LIBRARY_PATH="/usr/local/ssl/lib"
ENV PATH="/usr/local/ssl/bin:${PATH}"

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