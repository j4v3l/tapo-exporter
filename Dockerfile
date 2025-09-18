FROM python:3.13.7-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  build-essential \
  libffi-dev \
  python3-dev \
  && rm -rf /var/lib/apt/lists/*

# Create logs directory
RUN mkdir -p /var/log/tapo && \
  chmod 755 /var/log/tapo

# Update setuptools to a secure version
RUN pip install --upgrade setuptools

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_DIR=/var/log/tapo

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["python", "-m", "tapo_exporter"]