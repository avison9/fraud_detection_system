# Use a Python 3 base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy the entire app
COPY . /app

# Expose the port if needed (optional)
EXPOSE 5000

# Set the default command to run the consumer
CMD ["python", "fraud_detector_consumer.py"]
