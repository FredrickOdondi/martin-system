# Railway Frontend Deployment Guide

## Current Configuration

### Service Settings
- **Service Name**: `frontend`
- **Root Directory**: `/frontend`
- **Branch**: `main`
- **Builder**: Dockerfile
- **Port**: 8080

### Custom Domain
- **Domain**: `ecowasiisummit.net`
- **Target Port**: 8080

## Required Environment Variables

Set these in Railway's **Variables** section for the frontend service:

### Build-time Variables (Required)
```bash
VITE_API_URL=https://your-backend.railway.app
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_APP_NAME=Martin AI Summit Manager
VITE_APP_VERSION=1.0.0
```

### Runtime Variables
```bash
PORT=8080  # Railway sets this automatically
```

## Deployment Checklist

### 1. Environment Variables
- [ ] Set `VITE_API_URL` to your backend Railway URL
- [ ] Set `VITE_GOOGLE_CLIENT_ID` from Google Cloud Console
- [ ] Set `VITE_APP_NAME` and `VITE_APP_VERSION`
- [ ] Verify `PORT` is set to 8080

### 2. Build Configuration
- [ ] Confirm Root Directory is `/frontend`
- [ ] Confirm Builder is set to `DOCKERFILE`
- [ ] Confirm Dockerfile path is `Dockerfile`

### 3. Networking
- [ ] Set Target Port to `8080`
- [ ] Add custom domain `ecowasiisummit.net` pointing to port 8080
- [ ] Verify DNS records are configured for your domain

### 4. Deploy Settings
- [ ] Restart Policy: `ON_FAILURE`
- [ ] Max Restart Retries: `10`
- [ ] Replicas: `1` (or more for high availability)

## Troubleshooting

### Build Fails
- Check that all `VITE_*` environment variables are set
- Verify the Dockerfile path is correct
- Check build logs for missing dependencies

### App Not Accessible
- Verify Target Port matches the PORT in Dockerfile (8080)
- Check that nginx is starting correctly in logs
- Ensure custom domain DNS is properly configured

### API Calls Failing
- Verify `VITE_API_URL` points to the correct backend URL
- Check CORS settings on backend
- Verify backend is running and accessible

### Environment Variables Not Working
- Remember: `VITE_*` variables are baked into the build
- After changing `VITE_*` variables, you must **redeploy** (not just restart)
- Check browser console for the actual API URL being used

## Architecture

```
┌─────────────────┐
│   User Browser  │
└────────┬────────┘
         │
         │ HTTPS
         ▼
┌─────────────────────────┐
│  ecowasiisummit.net     │
│  (Railway Frontend)     │
│  ┌──────────────────┐   │
│  │  Nginx :8080     │   │
│  │  Serves React    │   │
│  │  SPA (dist/)     │   │
│  └──────────────────┘   │
└─────────┬───────────────┘
          │
          │ API Calls
          │ (VITE_API_URL)
          ▼
┌─────────────────────────┐
│  Backend Railway App    │
│  FastAPI + Workers      │
└─────────────────────────┘
```

## Important Notes

1. **Build Args**: The Dockerfile uses build args to inject `VITE_*` variables during build
2. **Port Binding**: Nginx listens on the `PORT` environment variable (default 8080)
3. **SPA Routing**: All routes are handled by React Router via nginx's `try_files`
4. **Static Assets**: Cached for 1 year with immutable cache headers
5. **Environment Variables**: `VITE_*` variables are **compile-time** only - they're baked into the JS bundle

## Deployment Commands

### Manual Deploy
```bash
# From project root
git add .
git commit -m "Update frontend"
git push origin main
```

Railway will automatically detect changes and redeploy.

### Force Redeploy
If you only changed environment variables:
1. Go to Railway Dashboard
2. Click on the frontend service
3. Go to latest deployment
4. Click "Redeploy" button

## Health Check

After deployment, verify:
1. Visit `https://ecowasiisummit.net` - should load the app
2. Check browser console for errors
3. Test login functionality
4. Verify API calls are reaching backend
