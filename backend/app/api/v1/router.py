from fastapi import APIRouter
from app.api.v1.endpoints import health, facilities, cases, assistant

api_v1_router = APIRouter()

# Include health check
api_v1_router.include_router(health.router, tags=["Health"])

# Include facilities and ASV endpoints
api_v1_router.include_router(facilities.router)

# Include emergency cases endpoints
api_v1_router.include_router(cases.router)

# Include shared conversational assistant endpoints
api_v1_router.include_router(assistant.router)


