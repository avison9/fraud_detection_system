FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc g++ libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m pip install --upgrade pip && pip install virtualenv

RUN python -m venv /app/venv

# Install Python dependencies
COPY requirements.txt /app/requirements.txt

RUN /app/venv/bin/python -m pip install --upgrade pip && /app/venv/bin/pip install -r /app/requirements.txt

RUN /app/venv/bin/pip list

# Copy all required project directories
COPY fraud_detector/ ./fraud_detector/

COPY data/ ./data/

COPY entrypoint.sh/ ./entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH="/app"


CMD ["/app/entrypoint.sh"]
