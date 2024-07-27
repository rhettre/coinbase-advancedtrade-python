# Use the Amazon Linux 2023 image compatible with AWS Lambda
FROM amazonlinux:2023

# Install Python 3 and ZIP
RUN yum install -y python3 python3-pip zip && \
    yum clean all

# Set up the work directory
WORKDIR /root

# Copy your application code and requirements.txt into the Docker image
COPY . .

# Install application and dependencies into a directory named 'python'
RUN pip3 install --upgrade pip && \
    pip3 install . --target python && \
    pip3 install -r requirements.txt --target python

# Package everything into a ZIP file
CMD ["zip", "-r", "layer.zip", "python"]