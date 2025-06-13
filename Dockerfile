# 🎼 Orchestra AI Docker Container
# Multi-stage build for production deployment

# Stage 1: Node.js build for frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci --only=production

COPY web/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libmagic1 \
    libpq-dev \
    gcc \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash orchestra
WORKDIR /home/orchestra/app

# Copy Python requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install additional production dependencies
RUN pip install --no-cache-dir gunicorn setproctitle

# Copy application code
COPY --chown=orchestra:orchestra api/ ./api/
COPY --chown=orchestra:orchestra mcp_servers/ ./mcp_servers/
COPY --chown=orchestra:orchestra shared/ ./shared/
COPY --chown=orchestra:orchestra orchestra_supervisor.py ./
COPY --chown=orchestra:orchestra claude_mcp_config.json ./

# Copy built frontend
COPY --from=frontend-builder --chown=orchestra:orchestra /app/web/dist ./web/dist/
COPY --chown=orchestra:orchestra web/public/ ./web/public/

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/orchestra.conf

# Create necessary directories
RUN mkdir -p logs data uploads backups && \
    chown -R orchestra:orchestra logs data uploads backups

# Set environment variables
ENV PYTHONPATH="/home/orchestra/app:/home/orchestra/app/api"
ENV ENVIRONMENT="production"
ENV DATABASE_URL="sqlite+aiosqlite:///home/orchestra/app/data/orchestra.db"
ENV UPLOAD_DIR="/home/orchestra/app/uploads"

# Switch to app user
USER orchestra

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health && \
        curl -f http://localhost:8000/api/health && \
        curl -f http://localhost:3002/ || exit 1

# Expose ports
EXPOSE 8000 8003 3002

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/orchestra.conf"] 