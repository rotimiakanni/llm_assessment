FROM python:3.11-slim

WORKDIR /app

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && apt-get clean

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY summarize.py .
COPY worker.py .

# Start Celery worker by default
CMD ["celery", "-A", "worker", "worker", "--loglevel=info"]
