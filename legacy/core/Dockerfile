FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements/base.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ .

# Run the FastAPI application
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000"]
