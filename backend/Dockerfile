# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# --- NEW: Install System Dependencies for OpenCV, PDF, and OCR ---
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    socat \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
# ------------------------------------------------------------------

# 2. Install Tailscale (Copy binaries from official image)
COPY --from=docker.io/tailscale/tailscale:stable /usr/local/bin/tailscaled /usr/local/bin/tailscaled
COPY --from=docker.io/tailscale/tailscale:stable /usr/local/bin/tailscale /usr/local/bin/tailscale
RUN mkdir -p /var/run/tailscale /var/cache/tailscale /var/lib/tailscale

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install "httpx[socks]" pysocks requests

COPY src/ backend/src/
ENV PYTHONPATH=/app

# Copy source code
RUN echo "--- Listing /app directory ---" && ls -R /app

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh


# Cloud Run injects the PORT env var
CMD ["/app/start.sh"]