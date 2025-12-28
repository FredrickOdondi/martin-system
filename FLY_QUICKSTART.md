# Fly.io Quick Start Guide
## Deploy in 10 Minutes!

This is the fastest way to get your ECOWAS app running on Fly.io.

---

## Prerequisites (2 minutes)

1. **Install Flyctl:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   flyctl auth login
   ```

---

## Deploy Backend (5 minutes)

```bash
# 1. Navigate to your project
cd "/Users/fredrickotieno/Desktop/Martins System"

# 2. Create the backend app (one-time)
flyctl launch --no-deploy
# Choose:
# - App name: martins-system-backend (or your choice)
# - Region: jnb (Johannesburg - closest to you)
# - PostgreSQL: No
# - Redis: No
# - Deploy now: No

# 3. Create database volume
flyctl volumes create ecowas_data --region jnb --size 1

# 4. Set required secrets
flyctl secrets set \
  SECRET_KEY="$(openssl rand -base64 32)" \
  JWT_SECRET_KEY="$(openssl rand -base64 32)"

# 5. Deploy!
flyctl deploy

# 6. Verify it's working
curl https://martins-system-backend.fly.dev/health
# Should return: {"status":"healthy"}
```

**Backend is live!** 🎉
- URL: https://martins-system-backend.fly.dev
- Docs: https://martins-system-backend.fly.dev/docs

---

## Deploy Frontend (3 minutes)

```bash
# 1. Navigate to frontend
cd frontend

# 2. Update API URL in fly.toml
# Edit frontend/fly.toml and set:
[env]
  VITE_API_URL = "https://martins-system-backend.fly.dev"

# 3. Create the frontend app (one-time)
flyctl launch --no-deploy
# Choose:
# - App name: martins-system-frontend (or your choice)
# - Region: jnb (Johannesburg)
# - Deploy now: No

# 4. Deploy!
flyctl deploy

# 5. Open in browser
flyctl apps open
```

**Frontend is live!** 🎉
- URL: https://martins-system-frontend.fly.dev

---

## Or Use Helper Scripts

We've created scripts to make this even easier:

```bash
# Deploy backend
./deploy-backend.sh

# Deploy frontend
./deploy-frontend.sh
```

The scripts will:
- ✅ Check prerequisites
- ✅ Create volumes if needed
- ✅ Generate and set secrets
- ✅ Deploy the app
- ✅ Show you the URLs

---

## What's Deployed?

| Component | URL | Description |
|-----------|-----|-------------|
| Backend API | https://martins-system-backend.fly.dev | FastAPI + SQLite |
| Frontend | https://martins-system-frontend.fly.dev | React App |
| API Docs | https://martins-system-backend.fly.dev/docs | Swagger UI |

---

## Useful Commands

```bash
# View logs
flyctl logs -a martins-system-backend
flyctl logs -a martins-system-frontend

# Check status
flyctl status -a martins-system-backend

# SSH into app
flyctl ssh console -a martins-system-backend

# View monitoring dashboard
flyctl dashboard

# Restart app
flyctl apps restart -a martins-system-backend
```

---

## Update Your App

After making code changes:

```bash
# Redeploy backend
flyctl deploy -a martins-system-backend

# Redeploy frontend
cd frontend && flyctl deploy -a martins-system-frontend
```

---

## Cost

**Your setup is FREE!** ✨

Fly.io free tier includes:
- 3 VMs (256MB each)
- 3GB storage
- Your setup uses 2 VMs + 1GB = within limits!

Apps auto-sleep when idle and wake up on requests.

---

## Troubleshooting

### Backend won't start?

```bash
# Check logs
flyctl logs -a martins-system-backend

# Common fix: Ensure secrets are set
flyctl secrets list -a martins-system-backend
```

### Frontend not connecting to backend?

Check `frontend/fly.toml`:
```toml
[env]
  VITE_API_URL = "https://your-backend-url.fly.dev"
```

### Need help?

See the full guide: [FLY_DEPLOYMENT.md](./FLY_DEPLOYMENT.md)

---

## Next Steps

1. **Test your app** - Create a user, upload documents
2. **Set up custom domain** (optional):
   ```bash
   flyctl certs add yourdomain.com
   ```
3. **Add API keys** for full features:
   ```bash
   flyctl secrets set \
     OPENAI_API_KEY="your-key" \
     ANTHROPIC_API_KEY="your-key"
   ```

---

**That's it! Your app is now live on Fly.io! 🚀**

For detailed information, see [FLY_DEPLOYMENT.md](./FLY_DEPLOYMENT.md)
