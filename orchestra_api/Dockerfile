# Orchestra API Dockerfile
# Optimized for Google Cloud Run with pip + requirements.txt workflow

FROM python:3.10-slim

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements files first for Docker layer caching
COPY ../requirements/base.txt ./requirements.txt

# Install Python dependencies using pip
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for Cloud Run
EXPOSE 8080

# Entrypoint for Cloud Run (use uvicorn directly)
CMD ["uvicorn", "orchestra_api.main:app", "--host", "0.0.0.0", "--port", "8080"]