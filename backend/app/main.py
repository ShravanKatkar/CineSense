import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from contextlib import asynccontextmanager

from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.health import router as health_router
from app.api.v1.movies import router as movies_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.system import router as system_router
from app.api.v1.users import router as users_router
from app.core.cache import cache_service
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.services.worker import ingestion_worker

setup_logging()
log = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager initializing cache tier and background worker."""
    await cache_service.init()
    await ingestion_worker.start()
    yield
    await ingestion_worker.stop()
    await cache_service.close()


app = FastAPI(
    title="CineSense AI Movie Recommendation & RAG API",
    description="Hybrid 5-level RecSys + Grounded RAG Movie Assistant API",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    log.warning("app_error", code=exc.code, status_code=exc.status_code, message=exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "status_code": exc.status_code,
            }
        },
    )


# Include API v1 Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(movies_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")

# Static assets & SPA fallback (mounted in production Docker)
from pathlib import Path
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Protect API routes and OpenAPI docs from catch-all fallback
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
            return JSONResponse(status_code=404, content={"error": {"code": "not_found", "message": "Endpoint not found"}})
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(STATIC_DIR / "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "name": "CineSense AI Engine API",
            "docs": "/docs",
            "health": "/api/v1/health",
            "version": settings.app_version,
        }

