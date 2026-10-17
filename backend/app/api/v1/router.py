from fastapi import APIRouter
from app.api.v1.endpoints import health, facilities

api_v1_router = APIRouter()

# Include health check
api_v1_router.include_router(health.router, tags=["Health"])

# Include facilities and ASV endpoints
api_v1_router.include_router(facilities.router)
