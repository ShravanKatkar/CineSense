import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.movies import router as movies_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.users import router as users_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging

setup_logging()
log = structlog.get_logger()
settings = get_settings()

app = FastAPI(
    title="CineSense AI Movie Recommendation & RAG API",
    description="Hybrid 5-level RecSys + Grounded RAG Movie Assistant API",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
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


@app.get("/")
async def root():
    return {
        "name": "CineSense AI Engine API",
        "docs": "/docs",
        "health": "/api/v1/health",
        "version": settings.app_version,
    }
