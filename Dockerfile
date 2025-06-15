# Orchestra AI Unified Platform Docker Container
# Production-ready Flask application with optimizations

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install production server
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY src/ ./src/
COPY database/ ./database/
COPY nginx/ ./nginx/
COPY monitoring/ ./monitoring/

# Create necessary directories
RUN mkdir -p logs data uploads src/database

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash orchestra && \
    chown -R orchestra:orchestra /app

# Switch to non-root user
USER orchestra

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=src/main.py
ENV FLASK_ENV=production

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "src.main:app"]
