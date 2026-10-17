from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.assistant import AssistantMessageRequest, AssistantMessageResponse
from app.services.assistant_service import assistant_service

router = APIRouter(prefix="/assistant", tags=["Shared Assistant"])


@router.post("/message", response_model=AssistantMessageResponse, status_code=status.HTTP_200_OK)
async def handle_assistant_message(
    payload: AssistantMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Unified conversational message endpoint for Edesy IVR, WhatsApp bot, and Flutter app.
    Maintains persistent conversation state, predicts intents, creates and updates
    emergency cases, identifies nearest facilities via spatial index, and issues referrals.
    """
    return await assistant_service.handle_message(payload, db)
