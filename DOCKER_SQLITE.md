# Docker Setup with SQLite
## ECOWAS Summit TWG Support System - Simplified!

## ✨ What Changed?

Your Docker setup now uses **SQLite** instead of PostgreSQL - much simpler!

### Benefits
- ✅ **No PostgreSQL needed** - One less service to worry about
- ✅ **Simpler setup** - Database is just a file
- ✅ **Easier backup** - Just copy the database file
- ✅ **Faster startup** - No waiting for PostgreSQL to initialize
- ✅ **Less memory** - SQLite is lightweight

---

## 🚀 Quick Start

**Same as before - just run**:
```bash
./docker-start.sh
```

Now only **3 main services** start:
1. **Redis** (cache & queue)
2. **Backend** (FastAPI with SQLite)
3. **Frontend** (React/Vite)

Plus optional Celery workers for background tasks.

---

## 📦 Services Running

| Service | Port | Database | Notes |
|---------|------|----------|-------|
| Frontend | 5173 | - | React UI |
| Backend | 8000 | SQLite | API with file-based DB |
| Redis | 6379 | - | Cache (optional) |

**Database Location**: `backend/data/ecowas_db.sqlite`

---

## 💾 Database Management

### Location
Your SQLite database is stored at:
```
backend/data/ecowas_db.sqlite
```

This file is mounted to the container, so your data persists even when containers restart!

### Backup
Super simple - just copy the file:
```bash
# Backup
cp backend/data/ecowas_db.sqlite backend/data/ecowas_db.backup.sqlite

# Or with timestamp
cp backend/data/ecowas_db.sqlite "backend/data/ecowas_db_$(date +%Y%m%d_%H%M%S).sqlite"
```

### Restore
```bash
# Restore from backup
cp backend/data/ecowas_db.backup.sqlite backend/data/ecowas_db.sqlite

# Then restart backend
docker-compose restart backend
```

### View Database
You can use SQLite tools to inspect the database:

```bash
# Using sqlite3 command line
sqlite3 backend/data/ecowas_db.sqlite

# Inside sqlite3
.tables          # List all tables
.schema users    # Show table structure
SELECT * FROM users;  # Query data
.quit            # Exit
```

Or use GUI tools like:
- [DB Browser for SQLite](https://sqlitebrowser.org/)
- [SQLiteStudio](https://sqlitestudio.pl/)

### Migrations
Migrations work the same:
```bash
docker exec -it ecowas-backend bash
alembic upgrade head
```

---

## 🔄 Switching Back to PostgreSQL

If you want PostgreSQL later:

1. **Edit `.env`**:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/db
   ```

2. **Uncomment PostgreSQL** in `docker-compose.yml`

3. **Restart**:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

---

## 📊 Performance

### SQLite is Great For:
- ✅ Development
- ✅ Small to medium applications (< 100K users)
- ✅ Single server deployments
- ✅ Read-heavy workloads
- ✅ Applications with < 100 concurrent connections

### Consider PostgreSQL For:
- 🔄 Very large datasets (> 100GB)
- 🔄 Many concurrent writes
- 🔄 Multi-server deployments
- 🔄 Complex queries and analytics

For most development and small production use cases, **SQLite is perfect**!

---

## 🎯 What You Get

All the same features:
- ✅ Full backend API
- ✅ React frontend
- ✅ Redis caching
- ✅ Celery background tasks
- ✅ Hot reload for development
- ✅ Auto-migrations
- ✅ Health checks

Just **simpler database setup**!

---

## 🆘 Troubleshooting

### Database locked error
SQLite can lock if multiple writes happen simultaneously.

**Solution**: This is rare. If it happens:
```bash
# Restart backend
docker-compose restart backend
```

### Database file not found
The database will be created automatically on first run!

If you see errors:
```bash
# Make sure data directory exists
mkdir -p backend/data

# Restart
docker-compose restart backend
```

### Want to reset database
```bash
# Delete database file
rm backend/data/ecowas_db.sqlite

# Restart - new database will be created
docker-compose restart backend
```

---

## 📝 Configuration

Your `.env` file now uses:
```bash
DATABASE_URL=sqlite+aiosqlite:///./data/ecowas_db.sqlite
```

That's it! No username, password, or host needed.

---

## ✅ Start Using It

1. **Start everything**:
   ```bash
   ./docker-start.sh
   ```

2. **Access the app**:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

3. **Check your database**:
   ```bash
   ls -lh backend/data/ecowas_db.sqlite
   ```

4. **Backup regularly**:
   ```bash
   cp backend/data/ecowas_db.sqlite backend/data/backup.sqlite
   ```

That's it! Much simpler than PostgreSQL! 🎉

---

## 🚀 Next Steps

- Start the app: `./docker-start.sh`
- Create your first user
- Upload some documents
- Your data is automatically saved to SQLite!

For full Docker documentation, see [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)
