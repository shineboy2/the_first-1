# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy unified requirements
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . /app

# Set working directory to API
WORKDIR /app/response-network/api

# Create export/import directories
RUN mkdir -p exports/settings exports/users imports/settings imports/users

# Set PYTHONPATH to include project root and API directory
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Use entrypoint script for initialization
ENTRYPOINT ["/app/entrypoint.sh"]
