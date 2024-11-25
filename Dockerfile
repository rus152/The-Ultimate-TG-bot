# Dockerfile

# Stage 1: Build
FROM python:3.12-slim AS build

WORKDIR /app

COPY requirements.txt .
RUN python -m venv venv && \
    ./venv/bin/pip install --upgrade pip && \
    ./venv/bin/pip install --prefer-binary --no-cache-dir -r requirements.txt

COPY main.py ./

# Stage 2: Run
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /root/.cache

WORKDIR /app

COPY --from=build /app/venv ./venv
COPY --from=build /app/main.py ./

ENV PATH="/app/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

CMD ["python", "main.py"]