from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.db.session import init_db, AsyncSessionLocal
from app.services.geo_service import geo_index
from app.services.facility_service import facility_service
from app.api.v1.router import api_v1_router
from app.api.v1.endpoints.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager: handles startup and shutdown."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")

    # 1. Initialize DB schema
    await init_db()

    # 2. Populate SQLite database from clean CSV if empty
    async with AsyncSessionLocal() as session:
        try:
            stats = await facility_service.import_baseline_data_if_empty(session)
            logger.info(f"Database facility status: {stats}")
        except Exception as e:
            logger.error(f"Error initializing facility database: {e}", exc_info=True)

    # 3. Load in-memory BallTree spatial index for sub-millisecond nearby search
    try:
        geo_index.load_from_file()
        logger.info(
            f"Spatial index ready: {geo_index.valid_count} facilities indexed for nearby search "
            f"({geo_index.quarantined_count} quarantined/missing coordinates excluded)."
        )
    except Exception as e:
        logger.error(f"Error building spatial index: {e}", exc_info=True)

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Common FastAPI backend for Dhwani-Sanjeevani, a voice-first snakebite emergency "
        "coordination system. Provides healthcare facility geolocation, unverified ASV "
        "status safety controls, and multi-channel integration readiness."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


# Root health endpoint for direct load balancer / monitoring pings
app.include_router(health_router, prefix="", tags=["Health"])

# API v1 routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_STR,
    }
