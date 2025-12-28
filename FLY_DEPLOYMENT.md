# Fly.io Deployment Guide
## ECOWAS Summit TWG Support System

Complete guide for deploying your full-stack application to Fly.io.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Deployment](#quick-deployment)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

---

## Prerequisites

### 1. Install Flyctl

```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Or via Homebrew
brew install flyctl
```

### 2. Login to Fly.io

```bash
flyctl auth login
```

### 3. Verify Installation

```bash
flyctl version
```

---

## Quick Deployment

### Deploy Backend (5 minutes)

```bash
# 1. Navigate to project root
cd "/Users/fredrickotieno/Desktop/Martins System"

# 2. Create volume for SQLite database
flyctl volumes create ecowas_data --region jnb --size 1

# 3. Deploy backend
flyctl deploy

# 4. Set required secrets
flyctl secrets set SECRET_KEY="your-super-secret-key-min-32-chars"
flyctl secrets set JWT_SECRET_KEY="your-jwt-secret-key-min-32-chars"

# 5. Check status
flyctl status
```

### Deploy Frontend (3 minutes)

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Deploy frontend
flyctl deploy

# 3. Check status
flyctl status
```

**Done!** Your app is live:
- Backend: https://martins-system-backend.fly.dev
- Frontend: https://martins-system-frontend.fly.dev

---

## Backend Deployment

### Step-by-Step Backend Setup

#### 1. Create Fly App (One-time)

```bash
# From project root
flyctl launch --no-deploy

# Follow prompts:
# - App name: martins-system-backend
# - Region: jnb (Johannesburg)
# - Don't deploy yet
```

#### 2. Create Persistent Volume for Database

```bash
# Create 1GB volume for SQLite database
flyctl volumes create ecowas_data --region jnb --size 1

# Verify volume created
flyctl volumes list
```

#### 3. Set Environment Secrets

```bash
# Required secrets
flyctl secrets set \
  SECRET_KEY="your-secret-key-minimum-32-characters-long-change-in-production" \
  JWT_SECRET_KEY="your-jwt-secret-key-minimum-32-characters-change-in-production"

# Optional API keys (for full functionality)
flyctl secrets set \
  OPENAI_API_KEY="your-openai-api-key" \
  ANTHROPIC_API_KEY="your-anthropic-api-key" \
  PINECONE_API_KEY="your-pinecone-api-key" \
  PINECONE_ENVIRONMENT="us-east-1" \
  PINECONE_INDEX_NAME="ecowas-summit-knowledge"
```

#### 4. Deploy Backend

```bash
# Deploy using Dockerfile.fly
flyctl deploy

# Watch deployment progress
# This will:
# - Build Docker image
# - Upload to Fly.io
# - Run migrations
# - Start the application
```

#### 5. Verify Backend

```bash
# Check status
flyctl status

# View logs
flyctl logs

# Test health endpoint
curl https://martins-system-backend.fly.dev/health

# Open API docs
flyctl apps open /docs
```

---

## Frontend Deployment

### Step-by-Step Frontend Setup

#### 1. Create Frontend App

```bash
# Navigate to frontend directory
cd frontend

# Launch app (one-time)
flyctl launch --no-deploy

# Follow prompts:
# - App name: martins-system-frontend
# - Region: jnb (Johannesburg)
# - Don't deploy yet
```

#### 2. Configure API URL

The frontend is pre-configured to use:
```
VITE_API_URL=https://martins-system-backend.fly.dev
```

If you used a different backend URL, update `frontend/fly.toml`:

```toml
[env]
  VITE_API_URL = "https://your-backend-url.fly.dev"
```

#### 3. Deploy Frontend

```bash
# From frontend directory
flyctl deploy

# This will:
# - Build the React app
# - Create optimized production bundle
# - Deploy to Nginx
```

#### 4. Verify Frontend

```bash
# Check status
flyctl status

# Open in browser
flyctl apps open

# View logs
flyctl logs
```

---

## Environment Variables

### Backend Environment Variables

Set via `flyctl secrets set`:

**Required:**
- `SECRET_KEY` - Application secret (32+ characters)
- `JWT_SECRET_KEY` - JWT signing key (32+ characters)

**Optional:**
- `OPENAI_API_KEY` - For OpenAI integration
- `ANTHROPIC_API_KEY` - For Claude integration
- `PINECONE_API_KEY` - For vector database
- `PINECONE_ENVIRONMENT` - Pinecone region (default: us-east-1)
- `PINECONE_INDEX_NAME` - Pinecone index name
- `SMTP_HOST` - Email server (for notifications)
- `SMTP_USERNAME` - Email username
- `SMTP_PASSWORD` - Email password

**View current secrets:**
```bash
flyctl secrets list
```

**Remove a secret:**
```bash
flyctl secrets unset SECRET_NAME
```

### Frontend Environment Variables

Set in `frontend/fly.toml`:

```toml
[env]
  VITE_API_URL = "https://your-backend-url.fly.dev"
  VITE_WS_URL = "wss://your-backend-url.fly.dev"
```

---

## Database Setup

### SQLite Database (Default)

Your app uses SQLite with a persistent volume.

**Volume Details:**
- Location: `/app/data`
- Database file: `/app/data/ecowas_db.sqlite`
- Size: 1GB (expandable)

**Backup Database:**

```bash
# SSH into the machine
flyctl ssh console

# Inside the container
cd /app/data
ls -lh ecowas_db.sqlite

# Exit
exit

# Download backup (from your machine)
flyctl ssh sftp get /app/data/ecowas_db.sqlite ./backup.sqlite
```

**Restore Database:**

```bash
# Upload database file
flyctl ssh sftp shell
put ./backup.sqlite /app/data/ecowas_db.sqlite
exit

# Restart app
flyctl apps restart
```

**Expand Volume:**

```bash
# Check current size
flyctl volumes list

# Extend volume (can only increase, not decrease)
flyctl volumes extend <volume-id> --size 2
```

### Run Migrations

Migrations run automatically on deployment. To run manually:

```bash
# SSH into the app
flyctl ssh console

# Run migrations
cd /app
alembic upgrade head

# Exit
exit
```

---

## Monitoring & Logs

### View Logs

```bash
# Real-time logs (all instances)
flyctl logs

# Last 100 lines
flyctl logs --tail 100

# Follow logs
flyctl logs -f

# Backend logs
flyctl logs -a martins-system-backend

# Frontend logs
flyctl logs -a martins-system-frontend
```

### Check Status

```bash
# App status
flyctl status

# Detailed info
flyctl info

# List all apps
flyctl apps list

# Check health
flyctl checks list
```

### SSH Access

```bash
# SSH into backend
flyctl ssh console -a martins-system-backend

# SSH into frontend
flyctl ssh console -a martins-system-frontend

# Run a command
flyctl ssh console -C "ls -la /app/data"
```

### Metrics & Monitoring

```bash
# Open monitoring dashboard
flyctl dashboard

# View metrics in terminal
flyctl vm status
```

---

## Troubleshooting

### App Won't Start

**Check logs:**
```bash
flyctl logs
```

**Common issues:**

1. **Missing secrets:**
   ```bash
   flyctl secrets list
   # Ensure SECRET_KEY and JWT_SECRET_KEY are set
   ```

2. **Database not accessible:**
   ```bash
   flyctl volumes list
   # Ensure volume is attached
   ```

3. **Port mismatch:**
   ```bash
   # Verify internal_port in fly.toml matches PORT env
   ```

### Database Issues

**SQLite locked:**
```bash
flyctl ssh console
cd /app/data
rm ecowas_db.sqlite-shm ecowas_db.sqlite-wal
exit
flyctl apps restart
```

**Reset database:**
```bash
flyctl ssh console
cd /app/data
rm ecowas_db.sqlite
exit
flyctl apps restart
# Migrations will create new database
```

### Frontend Not Loading

**Check backend URL:**
```bash
# Verify VITE_API_URL in frontend/fly.toml
# Should match your backend URL
```

**CORS issues:**
```bash
# SSH into backend
flyctl ssh console -a martins-system-backend

# Check CORS_ORIGINS includes frontend URL
# Should be set in backend env
```

### Deployment Fails

**Build fails:**
```bash
# Check Dockerfile.fly exists
ls -la Dockerfile.fly

# Try local build
docker build -f Dockerfile.fly -t test .
```

**Out of memory:**
```bash
# Increase memory in fly.toml
[[vm]]
  memory = '1gb'  # Increase from 512mb

# Redeploy
flyctl deploy
```

---

## Cost Optimization

### Free Tier

Fly.io free tier includes:
- Up to 3 shared-cpu-1x VMs (256MB RAM each)
- 3GB persistent volume storage
- 160GB outbound data transfer

Your setup uses:
- **Backend**: 1 VM (512MB) + 1GB volume
- **Frontend**: 1 VM (256MB)

**Total:** Within free tier limits!

### Auto-stop Machines

Your apps are configured to auto-stop when idle:

```toml
[http_service]
  auto_stop_machines = 'suspend'
  auto_start_machines = true
  min_machines_running = 0
```

This means:
- Apps sleep when inactive
- Wake up on first request (~1-2 second delay)
- **You only pay when apps are active**

### Reduce Costs

**1. Use smaller VMs:**
```toml
[[vm]]
  memory = '256mb'  # Instead of 512mb
```

**2. Share a volume:**
Backend and celery workers can share the same volume.

**3. Monitor usage:**
```bash
flyctl dashboard
# Check "Usage" tab
```

---

## Deployment Commands Reference

```bash
# Deploy
flyctl deploy                    # Deploy current directory
flyctl deploy --remote-only      # Build on Fly.io (faster)

# Secrets
flyctl secrets set KEY=value     # Set secret
flyctl secrets list              # List secrets
flyctl secrets unset KEY         # Remove secret

# Apps
flyctl status                    # Check status
flyctl apps list                 # List all apps
flyctl apps restart              # Restart app
flyctl apps destroy <app-name>   # Delete app

# Volumes
flyctl volumes list              # List volumes
flyctl volumes create NAME       # Create volume
flyctl volumes delete <id>       # Delete volume
flyctl volumes extend <id> --size 2  # Expand volume

# Logs & Monitoring
flyctl logs                      # View logs
flyctl logs -f                   # Follow logs
flyctl dashboard                 # Open dashboard
flyctl ssh console               # SSH into app

# Scaling
flyctl scale count 2             # Run 2 instances
flyctl scale memory 1024         # Set memory to 1GB

# Regions
flyctl regions list              # List all regions
flyctl regions add jnb           # Add region
```

---

## Next Steps

After deployment:

1. **Test your app:**
   - Backend API: https://martins-system-backend.fly.dev/docs
   - Frontend: https://martins-system-frontend.fly.dev

2. **Set up custom domain** (optional):
   ```bash
   flyctl certs add yourdomain.com
   ```

3. **Enable monitoring:**
   ```bash
   flyctl dashboard
   ```

4. **Backup database regularly:**
   ```bash
   flyctl ssh sftp get /app/data/ecowas_db.sqlite ./backups/backup-$(date +%Y%m%d).sqlite
   ```

5. **Set up CI/CD** (optional):
   - Use GitHub Actions for auto-deployment
   - See Fly.io docs for examples

---

## Support

- **Fly.io Docs**: https://fly.io/docs
- **Community Forum**: https://community.fly.io
- **Status Page**: https://status.fly.io

---

**Your app is now deployed and running on Fly.io! 🚀**
