# Use official Python slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
# Default config file (can override with -e CONFIG)
ENV org_FASTAPI_CONFIG=config.yaml

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
 && rm -rf /var/lib/apt/lists/*

# Copy application source code
COPY src/ src/

# Copy dependency file
COPY pyproject.toml ./

COPY README.md ./


# Install dependencies from pyproject.toml
RUN pip install --upgrade pip && pip install . --index-url https://git.org.ie/api/v4/projects/688/packages/pypi/simple

# Expose FastAPI default port
EXPOSE 8000

# Start the app with config from env
CMD ["sh", "-c", "python src/org_api/run.py --config=$org_FASTAPI_CONFIG"]
