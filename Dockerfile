# Use the Amazon Linux 2023 image compatible with AWS Lambda
FROM amazonlinux:2023

# Install Python 3.9 and ZIP
RUN dnf install -y python3.9 python3.9-pip zip && \
    dnf clean all

# Set up the work directory
WORKDIR /root

# Copy your application code and requirements.txt into the Docker image
COPY . .

# Install application and dependencies into a directory named 'python'
RUN python3.9 -m pip install --upgrade pip && \
    python3.9 -m pip install . --target python && \
    python3.9 -m pip install -r requirements.txt --target python

# Package everything into a ZIP file
CMD ["zip", "-r", "layer.zip", "python"]