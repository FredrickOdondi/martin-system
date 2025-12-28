# Docker Quick Start Guide
## ECOWAS Summit TWG Support System

## 🚀 Get Started in 3 Steps

### 1. Start the Application

```bash
./docker-start.sh
```

This single command will:
- ✅ Start PostgreSQL database
- ✅ Start Redis cache
- ✅ Start Backend API
- ✅ Start Frontend UI
- ✅ Start Celery workers
- ✅ Run database migrations

### 2. Access the Application

Once all services are running:

- **Frontend (Main App)**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. Stop the Application

```bash
./docker-stop.sh
```

Or press `Ctrl+C` if running in foreground.

---

## 📋 What's Running?

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5173 | React app with live reload |
| Backend | 8000 | FastAPI with auto-reload |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache & queue |
| Celery Worker | - | Background tasks |
| Celery Beat | - | Scheduled tasks |

---

## 🔧 Common Commands

```bash
# View logs for all services
./docker-logs.sh

# View logs for specific service
./docker-logs.sh backend
./docker-logs.sh frontend

# Clean up everything (including data)
./docker-clean.sh

# Start in background
docker-compose up -d

# Rebuild and start
docker-compose up --build
```

---

## ⚙️ Configuration

### First Time Setup

The `.env` files are already created with default values. For production, update:

1. **Root `.env` file**:
   - `POSTGRES_PASSWORD` - Change from default
   - `SECRET_KEY` - Use a strong secret key
   - `JWT_SECRET_KEY` - Use a strong JWT secret

2. **Optional API Keys** (for full functionality):
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `PINECONE_API_KEY`

### Edit Configuration

```bash
# Edit root configuration
nano .env

# Edit frontend configuration
nano frontend/.env

# Edit backend configuration
nano backend/.env
```

---

## 🐛 Troubleshooting

### Port Already in Use

If you see "port is already allocated":

1. Edit `.env` and change the port:
   ```bash
   FRONTEND_PORT=5174  # or any available port
   BACKEND_PORT=8001   # or any available port
   ```

2. Restart:
   ```bash
   docker-compose down
   docker-compose up
   ```

### Services Not Starting

```bash
# Check which services are running
docker-compose ps

# View logs for failing service
docker-compose logs [service-name]

# Examples:
docker-compose logs backend
docker-compose logs postgres
docker-compose logs frontend
```

### Database Issues

```bash
# Reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up
```

### Code Changes Not Reflecting

Both frontend and backend have hot reload enabled:

- **Frontend**: Changes in `frontend/src/` appear immediately
- **Backend**: Changes in `backend/app/` trigger auto-reload

If changes don't appear, check the logs:
```bash
./docker-logs.sh frontend
./docker-logs.sh backend
```

---

## 📚 Full Documentation

For detailed documentation, see [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)

Topics covered:
- Architecture overview
- Database management
- Backup & restore
- Production deployment
- Advanced configuration
- Complete troubleshooting guide

---

## 🎯 Development Workflow

1. **Start services**: `./docker-start.sh`
2. **Code changes**: Edit files in `frontend/src/` or `backend/app/`
3. **View logs**: `./docker-logs.sh [service]`
4. **Stop services**: `./docker-stop.sh`

### Hot Reload Active

- Frontend (Vite): Instant updates
- Backend (Uvicorn): Auto-reload on save

---

## 🔗 Quick Links

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Redoc Docs: http://localhost:8000/redoc

---

## ✅ Success Checklist

After running `./docker-start.sh`, verify:

- [ ] All 6 services started successfully
- [ ] Frontend accessible at http://localhost:5173
- [ ] Backend health check: http://localhost:8000/health returns `{"status":"healthy"}`
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] No error messages in logs

---

## 🆘 Need Help?

1. Check logs: `./docker-logs.sh [service]`
2. Read [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)
3. Review error messages carefully
4. Ensure Docker and Docker Compose are installed and running

---

**Happy Coding! 🎉**
