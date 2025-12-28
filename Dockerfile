# Multi-stage Dockerfile for ECOWAS Summit Application
# Builds both frontend and backend in a single container

FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Install frontend dependencies
COPY frontend/package*.json ./
RUN npm ci

# Build frontend
COPY frontend/ ./
RUN npm run build

# Main backend image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist /var/www/html

# Configure nginx for frontend
RUN echo 'server { \
    listen 80; \
    root /var/www/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://localhost:8000; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_cache_bypass $http_upgrade; \
    } \
}' > /etc/nginx/sites-available/default

# Create necessary directories
RUN mkdir -p /app/data /app/storage /app/logs /app/uploads /app/credentials /app/chroma_data

# Expose ports
EXPOSE 80 8000

# Start script
COPY <<'EOF' /app/start.sh
#!/bin/bash
set -e

# Start nginx in background
nginx

# Run database migrations
alembic upgrade head || echo "Migration failed or already up to date"

# Start backend
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
