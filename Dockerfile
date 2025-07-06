# Dockerfile

# Stage 1: Build
FROM pytorch/pytorch:2.4.0-cuda11.8-cudnn9-runtime AS build

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN python -m venv venv && \
    ./venv/bin/pip install --upgrade pip && \
    ./venv/bin/pip install --prefer-binary --no-cache-dir -r requirements.txt

# Copy source code
COPY *.py ./
COPY asr/ ./asr/

# Stage 2: Production runtime
FROM pytorch/pytorch:2.4.0-cuda11.8-cudnn9-runtime AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /root/.cache/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

WORKDIR /app

# Copy Python environment and source code from build stage
COPY --from=build /app/venv ./venv
COPY --from=build /app/*.py ./
COPY --from=build /app/asr ./asr

# Create directories for voice files
RUN mkdir -p voice_messages video_notes logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH="/app/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the application
CMD ["python", "main.py"]