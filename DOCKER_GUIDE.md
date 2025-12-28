# Docker Deployment Guide
## ECOWAS Summit TWG Support System

This guide provides comprehensive instructions for running the entire ECOWAS Summit TWG System using Docker.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Services Overview](#services-overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Running the Application](#running-the-application)
- [Development Workflow](#development-workflow)
- [Data Management](#data-management)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## Quick Start

Start the entire application with one command:

```bash
./docker-start.sh
```

Or manually:

```bash
docker-compose up --build
```

That's it! The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

To stop all services:

```bash
./docker-stop.sh
```

Or press `Ctrl+C` if running in foreground.

---

## Services Overview

The Docker setup includes 6 services:

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| **Frontend** | ecowas-frontend | 5173 | React application with Vite dev server |
| **Backend** | ecowas-backend | 8000 | FastAPI REST API |
| **PostgreSQL** | ecowas-postgres | 5432 | Primary database |
| **Redis** | ecowas-redis | 6379 | Cache & message broker |
| **Celery Worker** | ecowas-celery-worker | - | Background task processor |
| **Celery Beat** | ecowas-celery-beat | - | Scheduled task scheduler |

### Architecture Diagram

```
┌─────────────────┐
│   Frontend      │ :5173
│   (React/Vite)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend API   │ :8000
│   (FastAPI)     │
└────┬───────┬────┘
     │       │
     ▼       ▼
┌─────────┐ ┌─────────┐
│ Postgres│ │  Redis  │
│  :5432  │ │  :6379  │
└─────────┘ └────┬────┘
                 │
     ┌───────────┴───────────┐
     ▼                       ▼
┌──────────┐         ┌──────────┐
│  Celery  │         │  Celery  │
│  Worker  │         │   Beat   │
└──────────┘         └──────────┘
```

---

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher

Check your versions:

```bash
docker --version
docker-compose --version
```

### System Requirements

- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: At least 5GB free
- **CPU**: 2+ cores recommended

---

## Environment Setup

### 1. Root Environment File

The root `.env` file is already created with default values. Update the following critical settings:

```bash
# Edit .env file
nano .env
```

**Required changes**:

```bash
# Database credentials (IMPORTANT: Change in production)
POSTGRES_PASSWORD=your_secure_password_here

# Security keys (IMPORTANT: Change in production)
SECRET_KEY=your-secret-key-minimum-32-characters-long
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-characters
```

**Optional changes**:

```bash
# Ports (if you have conflicts)
BACKEND_PORT=8000
FRONTEND_PORT=5173
POSTGRES_PORT=5432
REDIS_PORT=6379

# External API keys (for full functionality)
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
PINECONE_API_KEY=your-pinecone-key-here
```

### 2. Frontend Environment File

The `frontend/.env` file is already created. You can modify it if needed:

```bash
# Edit frontend/.env
nano frontend/.env
```

Defaults:
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_MAX_FILE_SIZE=10485760
```

### 3. Backend Environment File

The `backend/.env` file contains backend-specific configuration. It's already set up to work with Docker.

---

## Running the Application

### Option 1: Using Helper Scripts (Recommended)

**Start all services**:
```bash
./docker-start.sh
```

This script will:
1. Check for missing `.env` files and create them if needed
2. Build all Docker images
3. Start all 6 services
4. Show logs in real-time

**Stop all services**:
```bash
./docker-stop.sh
```

**View logs**:
```bash
# All services
./docker-logs.sh

# Specific service
./docker-logs.sh backend
./docker-logs.sh frontend
./docker-logs.sh postgres
```

**Clean up** (removes all data):
```bash
./docker-clean.sh
```

### Option 2: Using Docker Compose Directly

**Start in foreground** (see logs):
```bash
docker-compose up --build
```

**Start in background**:
```bash
docker-compose up -d --build
```

**Stop services**:
```bash
docker-compose down
```

**View logs**:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Rebuild specific service**:
```bash
docker-compose up -d --build backend
```

---

## Development Workflow

### Hot Reload

Both frontend and backend support hot reload:

- **Frontend**: Edit files in `frontend/src/` - changes appear immediately
- **Backend**: Edit files in `backend/app/` - server reloads automatically

### Running Commands Inside Containers

**Backend shell**:
```bash
docker exec -it ecowas-backend bash

# Inside container
python manage.py migrate
alembic upgrade head
```

**Frontend shell**:
```bash
docker exec -it ecowas-frontend sh

# Inside container
npm install new-package
npm run build
```

**Database access**:
```bash
docker exec -it ecowas-postgres psql -U ecowas_user -d ecowas_summit_db

# Inside psql
\dt                    # List tables
SELECT * FROM users;   # Query data
\q                     # Exit
```

**Redis CLI**:
```bash
docker exec -it ecowas-redis redis-cli

# Inside redis-cli
PING                   # Test connection
KEYS *                 # List all keys
GET somekey            # Get value
```

### Database Migrations

Migrations run automatically on backend startup. To run manually:

```bash
docker exec -it ecowas-backend bash
alembic upgrade head
```

To create a new migration:

```bash
docker exec -it ecowas-backend bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

---

## Data Management

### Persistent Volumes

Data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls | grep ecowas

# Inspect a volume
docker volume inspect martins-system_postgres_data
```

### Backup Database

```bash
# Backup PostgreSQL
docker exec ecowas-postgres pg_dump -U ecowas_user ecowas_summit_db > backup.sql

# Backup with Docker
docker run --rm \
  --volumes-from ecowas-postgres \
  -v $(pwd):/backup \
  postgres:15-alpine \
  pg_dump -U ecowas_user ecowas_summit_db > /backup/db_backup.sql
```

### Restore Database

```bash
# Restore from backup
docker exec -i ecowas-postgres psql -U ecowas_user ecowas_summit_db < backup.sql
```

### Upload Files

Uploaded files are stored in `./uploads` directory and are mounted to containers. They persist even if containers are recreated.

---

## Troubleshooting

### Port Conflicts

**Error**: `Port 5173 is already allocated`

**Solution**:
1. Update port in `.env`:
   ```bash
   FRONTEND_PORT=5174
   ```
2. Restart:
   ```bash
   docker-compose down
   docker-compose up
   ```

### Database Connection Issues

**Error**: `could not connect to server`

**Solution**:
1. Check PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```
2. Check logs:
   ```bash
   docker-compose logs postgres
   ```
3. Reset database:
   ```bash
   docker-compose down -v
   docker-compose up
   ```

### Frontend Not Updating

**Issue**: Changes to frontend code not reflecting

**Solution**:
1. Ensure Vite dev server is running:
   ```bash
   docker-compose logs frontend
   ```
2. Rebuild frontend:
   ```bash
   docker-compose up -d --build frontend
   ```
3. Clear browser cache

### Backend Errors

**Check backend logs**:
```bash
docker-compose logs backend
```

**Common issues**:

1. **Module not found**: Rebuild container
   ```bash
   docker-compose up -d --build backend
   ```

2. **Database not initialized**: Check init script
   ```bash
   docker exec -it ecowas-backend cat /app/scripts/init_db.sh
   ```

3. **Permission denied**: Make scripts executable
   ```bash
   chmod +x backend/scripts/*.sh
   docker-compose up -d --build backend
   ```

### Celery Not Running

**Check workers**:
```bash
docker-compose logs celery_worker
docker-compose logs celery_beat
```

**Restart workers**:
```bash
docker-compose restart celery_worker celery_beat
```

### Out of Disk Space

**Clean up Docker**:
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

---

## Advanced Usage

### Scaling Services

Run multiple Celery workers:

```bash
docker-compose up -d --scale celery_worker=3
```

### Custom Network Configuration

Services communicate on `ecowas-network`. To inspect:

```bash
docker network inspect martins-system_ecowas-network
```

### Production Deployment

For production, update:

1. **Environment variables**:
   ```bash
   NODE_ENV=production
   PYTHON_ENV=production
   DEBUG=false
   ```

2. **Frontend target**:
   ```yaml
   # In docker-compose.yml
   frontend:
     target: production  # Instead of development
   ```

3. **Remove reload flags**:
   ```yaml
   # Remove --reload from backend command
   command: uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Monitoring

**View resource usage**:
```bash
docker stats
```

**Health checks**:
```bash
# Backend
curl http://localhost:8000/health

# PostgreSQL
docker exec ecowas-postgres pg_isready

# Redis
docker exec ecowas-redis redis-cli ping
```

### Accessing Services from Host

All services are accessible from your host machine:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### Docker Compose Override

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'

services:
  backend:
    volumes:
      - ./custom:/app/custom
    environment:
      - CUSTOM_VAR=value
```

This file is ignored by git and won't affect other developers.

---

## Useful Commands Reference

```bash
# Start services
./docker-start.sh                           # Using helper script
docker-compose up                           # Foreground
docker-compose up -d                        # Background
docker-compose up -d --build                # Rebuild and start

# Stop services
./docker-stop.sh                            # Using helper script
docker-compose down                         # Stop containers
docker-compose down -v                      # Stop and remove volumes

# View logs
./docker-logs.sh                            # All services
./docker-logs.sh backend                    # Specific service
docker-compose logs -f backend              # Follow logs

# Execute commands
docker exec -it ecowas-backend bash         # Backend shell
docker exec -it ecowas-frontend sh          # Frontend shell
docker exec -it ecowas-postgres psql -U ecowas_user ecowas_summit_db  # Database

# Service management
docker-compose restart backend              # Restart service
docker-compose ps                           # List services
docker-compose top                          # Show running processes

# Cleanup
./docker-clean.sh                           # Full cleanup script
docker-compose down -v                      # Remove volumes
docker system prune -a                      # Clean Docker system
```

---

## Support

For issues or questions:

1. Check logs: `./docker-logs.sh [service]`
2. Review this guide
3. Check official documentation:
   - [Docker Docs](https://docs.docker.com)
   - [Docker Compose](https://docs.docker.com/compose)
4. Create an issue in the project repository

---

## Next Steps

1. Start the application: `./docker-start.sh`
2. Access frontend: http://localhost:5173
3. Check API docs: http://localhost:8000/docs
4. Review and update `.env` configuration
5. Begin development with hot reload enabled

Happy coding! 🚀
