FROM public.ecr.aws/lambda/python:3.9

WORKDIR /var/task

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install . && \
    mkdir -p /tmp/python && \
    pip install \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.9 \
        --only-binary=:all: --upgrade \
        -r requirements.txt -t /tmp/python && \
    pip install . -t /tmp/python && \
    cd /tmp/python && \
    find . -type d -name "__pycache__" -exec rm -rf {} + && \
    zip -r9 /tmp/layer.zip .

CMD ["python3", "-m", "awslambdaric", "handler.lambda_handler"]