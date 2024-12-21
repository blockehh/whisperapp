# Dockerfile
FROM python:3.9-slim

# Install system dependencies needed for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (Flask, Faster Whisper, etc.)
RUN pip install --no-cache-dir \
    flask==2.3.2 \
    werkzeug==2.3.5 \
    faster-whisper==0.6.0

# Create /app directory
WORKDIR /app

# Copy application code
COPY whisperapp.py /app/
COPY templates/ /app/templates/

# Expose port 5000
EXPOSE 5000

# Run the Flask app
CMD ["python", "whisperapp.py"]
