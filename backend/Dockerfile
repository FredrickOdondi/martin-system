# Backend Dockerfile for Railway deployment
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

# Set work directory to backend
WORKDIR /app/backend

# Install system dependencies
# Removed python3-* packages to avoid conflicts with Docker image python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the backend directory contents
COPY . .

# Create uploads directory and set permissions
RUN mkdir -p /app/backend/uploads && \
    chmod -R 777 /app/backend/uploads

# Expose port (Railway will set PORT env variable)
EXPOSE ${PORT:-8000}

# Default command can be overridden by Railway Service settings
# to run either web server or celery worker
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
