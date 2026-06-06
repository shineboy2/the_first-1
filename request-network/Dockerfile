FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    postgresql-client \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api /app

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Setup directories for exports/imports and create non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN mkdir -p /app/exports /app/imports /app/shared_data
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Use entrypoint script for initialization before starting the app
ENTRYPOINT ["/app/entrypoint.sh"]
