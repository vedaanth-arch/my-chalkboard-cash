# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies (Tesseract for OCR and libs for OpenCV/Pillow)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Default port; Render provides $PORT at runtime
ENV PORT=5000

# Start Flask app with Gunicorn, binding to $PORT
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT:-5000} app:app"]
