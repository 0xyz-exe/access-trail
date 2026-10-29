"""FastAPI main application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.db.session import init_db
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.identities import router as identities_router
from backend.app.api.v1.permissions import router as permissions_router
from backend.app.api.v1.reviews import router as reviews_router
from backend.app.api.v1.revocations import router as revocations_router
from backend.app.api.v1.findings import router as findings_router
from backend.app.api.v1.policies import router as policies_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.connectors import router as connectors_router
from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.reports import router as reports_router
from backend.app.api.v1.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite or Postgres tables on startup
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Identity, Access Review & Permission Audit Platform",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permissive in dev/local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz", tags=["health"])
@app.get("/api/v1/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "service": "AccessTrail",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0"
    }

# Register API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(identities_router, prefix=settings.API_V1_STR)
app.include_router(permissions_router, prefix=settings.API_V1_STR)
app.include_router(reviews_router, prefix=settings.API_V1_STR)
app.include_router(revocations_router, prefix=settings.API_V1_STR)
app.include_router(findings_router, prefix=settings.API_V1_STR)
app.include_router(policies_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(connectors_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)

# Serve static frontend in production
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import BASE_DIR

frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static_frontend")
