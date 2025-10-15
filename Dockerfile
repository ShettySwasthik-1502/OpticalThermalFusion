# Dockerfile - for hosting your Flask + OpenCV backend
FROM python:3.11-slim

# Install system libs OpenCV may need (libgl, libglib). Adjust if errors indicate missing libs.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app

# default port (can be overridden by Render's $PORT env)
ENV PORT=5000
EXPOSE 5000

# Use shell form so $PORT is expanded at runtime (Render injects PORT)
CMD gunicorn --bind 0.0.0.0:$PORT server.app:app --workers 1 --threads 4 --timeout 120
