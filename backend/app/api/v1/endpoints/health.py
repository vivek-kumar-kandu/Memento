from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.geo_service import geo_index

router = APIRouter()


@router.get(
    "/health",
    summary="Service Health and Data Index Status",
    description="Returns operational status of the backend API, SQLite database, and in-memory spatial index.",
    response_model=Dict[str, Any],
)
async def check_health(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" and geo_index.is_loaded else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": db_status,
            "engine": "sqlite+aiosqlite",
        },
        "facility_index": {
            "status": "ready" if geo_index.is_loaded else "not_loaded",
            "valid_indexed_facilities": geo_index.valid_count,
            "quarantined_facilities_excluded": geo_index.quarantined_count,
            "total_source_facilities": geo_index.total_source_count,
            "asv_baseline_status": "100% UNKNOWN (unverified)",
        },
    }
