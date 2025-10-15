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

# Copy requirements and install (use the final requirements.txt you provided)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app

# Expose the port (Render / Railway provide $PORT env variable)
ENV PORT=5000
EXPOSE 5000

# Use gunicorn for production-grade serving of Flask app (server.app:app)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "server.app:app", "--workers", "1", "--threads", "4", "--timeout", "120"]
