from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.routes import twgs, meetings, auth, projects, action_items, documents, audit, agents, dashboard, users, notifications

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
    logger = logging.getLogger("uvicorn.info")
    logger.info("--- STARTUP DIAGNOSTICS ---")
    logger.info(f"API_V1_STR: {settings.API_V1_STR}")
    logger.info(f"CORS_ORIGINS: {cors_origins}")
    
    logger.info("REGISTERED ROUTES:")
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    for route in url_list:
        logger.info(f"  {route['path']} ({route['name']})")
    logger.info("--- END STARTUP DIAGNOSTICS ---")

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

@app.get("/")
async def root():
    return {"message": "Welcome to the ECOWAS Summit TWG Support System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
