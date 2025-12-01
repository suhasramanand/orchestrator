FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install numpy for matrix operations (optional, can be removed if not needed)
RUN pip install --no-cache-dir numpy

# Copy worker code
COPY worker.py .

# Run worker
CMD ["python", "worker.py"]

