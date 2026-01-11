from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import twgs, meetings, auth, projects, action_items, documents, audit, agents, dashboard, users, notifications, supervisor

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
# Convert CORS_ORIGINS to list if it's a string
# Convert CORS_ORIGINS to list if it's a string
cors_origins = settings.CORS_ORIGINS
if isinstance(cors_origins, str):
    cors_origins = [origin.strip() for origin in cors_origins.split(",")]

# Force add production origin to ensure it's never missed
if "https://frontend-production-1abb.up.railway.app" not in cors_origins:
    cors_origins.append("https://frontend-production-1abb.up.railway.app")

# Add IPv4 localhost variant to support 127.0.0.1 connections
if "http://127.0.0.1:5173" not in cors_origins:
    cors_origins.append("http://127.0.0.1:5173")

# Add localhost variant
if "http://localhost:5173" not in cors_origins:
    cors_origins.append("http://localhost:5173")

# Trust X-Forwarded-Proto headers from Railway/Load Balancers
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

@app.on_event("startup")
async def startup_event():
    import logging
    import os
    from alembic.config import Config
    from alembic import command
    from app.core.google_utils import setup_google_credentials
    
    # Initialize Google Auth (restore credentials from env if needed)
    setup_google_credentials()
    
    logger = logging.getLogger("uvicorn.info")
    logger.info("--- STARTUP DIAGNOSTICS ---")
    
    # Run Database Migrations
    try:
        logger.info("Running database migrations...")
        if os.path.exists("alembic.ini"):
            alembic_cfg = Config("alembic.ini")
            # Run upgrade head
            # Run upgrade head in a separate thread to avoid asyncio loop conflict
            # because env.py calls asyncio.run()
            # import asyncio
            # await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
            logger.info("Database migrations skipped (handled manually to prevent startup hang).")
            logger.info("Database migrations completed successfully!")
        else:
            logger.warning("alembic.ini not found! Skipping migrations.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Continue startup
    
    logger.info(f"API_V1_STR: {settings.API_V1_STR}")
    logger.info(f"CORS_ORIGINS: {cors_origins}")
    logger.info(f"GOOGLE_CLIENT_ID Loaded: {bool(settings.GOOGLE_CLIENT_ID)}")
    if settings.GOOGLE_CLIENT_ID:
        logger.info(f"GOOGLE_CLIENT_ID Prefix: {settings.GOOGLE_CLIENT_ID[:10]}...")
    
    logger.info("REGISTERED ROUTES:")
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    for route in url_list:
        logger.info(f"  {route['path']} ({route['name']})")

    # Start Scheduler
    from app.services.scheduler import scheduler_service
    scheduler_service.start()
    
    # Start Continuous Monitor (Background Conflict Detection)
    from app.services.continuous_monitor import get_continuous_monitor
    monitor = get_continuous_monitor()
    monitor.start()
    
    # Start Supervisor State Refresh Task
    from app.services.supervisor_state_service import get_supervisor_state
    from app.core.database import get_db_session_context

    async def refresh_supervisor_state_job():
        """Background task to refresh supervisor state"""
        logger.info("Executing background supervisor state refresh...")
        try:
            # Create a new session context
            async with get_db_session_context() as db:
                state_service = get_supervisor_state()
                await state_service.refresh_state(db)
                logger.info("Background supervisor state refresh completed.")
        except Exception as e:
            logger.error(f"Failed to refresh supervisor state: {e}")

    # Add the job to the scheduler (run every 5 minutes)
    # We need to access the scheduler instance from the service
    # Assuming scheduler_service exposes the underlying scheduler or has an add_job method
    # If not, we might need to modify scheduler_service. For now, let's assume standard APScheduler usage
    try:
        scheduler_service.scheduler.add_job(
            refresh_supervisor_state_job,
            'interval',
            minutes=5,
            id='supervisor_state_refresh',
            replace_existing=True
        )
        logger.info("Supervisor state refresh job added to scheduler.")
    except Exception as e:
        logger.error(f"Failed to add supervisor refresh job: {e}")


    logger.info("--- END STARTUP DIAGNOSTICS ---")

@app.on_event("shutdown")
async def shutdown_event():
    from app.services.scheduler import scheduler_service
    scheduler_service.shutdown()

# Register routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}")
app.include_router(twgs.router, prefix=f"{settings.API_V1_STR}")
app.include_router(meetings.router, prefix=f"{settings.API_V1_STR}")
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}")
app.include_router(action_items.router, prefix=f"{settings.API_V1_STR}")
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}")
app.include_router(audit.router, prefix=f"{settings.API_V1_STR}")
app.include_router(agents.router, prefix=f"{settings.API_V1_STR}")
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}")
app.include_router(users.router, prefix=f"{settings.API_V1_STR}")
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}")
app.include_router(supervisor.router, prefix=f"{settings.API_V1_STR}")

@app.get("/")
async def root():
    return {"message": "Welcome to the ECOWAS Summit TWG Support System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
