# Use the Amazon Linux 2023 image compatible with AWS Lambda
FROM amazonlinux:2023

# Install Python 3, pip, and other necessary tools
RUN dnf install -y python3 python3-pip zip && \
    dnf clean all

# Set up the work directory
WORKDIR /root

# Copy your application code and requirements.txt into the Docker image
COPY . .

# Create and activate a virtual environment, then install dependencies
RUN python3 -m venv /root/venv && \
    . /root/venv/bin/activate && \
    pip install --upgrade pip && \
    pip install . && \
    pip install -r requirements.txt && \
    deactivate

# Package everything into a ZIP file
CMD . /root/venv/bin/activate && \
    mkdir python && \
    pip install . -t python && \
    pip install -r requirements.txt -t python && \
    zip -r layer.zip python && \
    deactivate