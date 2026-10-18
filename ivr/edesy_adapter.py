import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

try:
    from config import EDESY_WEBHOOK_SECRET
    from conversation import ConversationController
except ImportError:
    from .config import EDESY_WEBHOOK_SECRET
    from .conversation import ConversationController

logger = logging.getLogger("ivr.edesy_adapter")

router = APIRouter(prefix="/api/v1/edesy", tags=["Edesy IVR Provider"])


class EdesyWebhookEvent(BaseModel):
    """Schema for asynchronous Edesy call lifecycle webhook events."""
    event_type: str = Field(..., description="Lifecycle event: call.initiated, call.answered, call.ended, etc.")
    call_sid: str = Field(..., description="Unique telephony call identifier from Edesy")
    from_number: Optional[str] = Field(default=None, description="Caller phone number")
    to_number: Optional[str] = Field(default=None, description="Dialed IVR helpline number")
    recording_url: Optional[str] = Field(default=None, description="Audio recording URL if available")
    duration_seconds: Optional[int] = Field(default=None, description="Call duration in seconds")
    timestamp: Optional[str] = Field(default=None, description="Event timestamp")


class EdesyToolRequest(BaseModel):
    """
    Schema for synchronous in-conversation tool calls from Edesy's voice agent.
    Accepts both standard and common telephony parameter naming.
    """
    call_sid: str = Field(..., description="Call session identifier")
    transcript: Optional[str] = Field(default=None, description="Transcribed caller utterance from Edesy STT")
    message: Optional[str] = Field(default=None, description="Alternative field for transcript")
    caller_phone: Optional[str] = Field(default=None, description="Caller telephone number")
    language: Optional[str] = Field(default="en", description="Language code (en, hi)")


class EdesyToolResponse(BaseModel):
    """Schema for synchronous response returned to Edesy voice bot."""
    response_text: str = Field(..., description="Spoken prompt for Edesy TTS to synthesize")
    next_action: str = Field(..., description="Conversation action: CONTINUE, COLLECT_LOCATION, ESCALATE_HUMAN, END_CALL")
    end_call: bool = Field(default=False, description="Whether telephony engine should hang up")
    conversation_id: Optional[str] = Field(default=None, description="Backend conversation ID")
    case_id: Optional[str] = Field(default=None, description="Backend emergency case ID")
    language: Optional[str] = Field(default="hindi", description="Detected caller language (hindi, hinglish, bhojpuri)")



def get_controller(request: Request) -> ConversationController:
    """Helper to access global ConversationController instance from FastAPI state."""
    return getattr(request.app.state, "conversation_controller", ConversationController())


@router.post(
    "/webhook",
    summary="Edesy Asynchronous Call Lifecycle Webhook",
    description=(
        "Receives asynchronous telephony events (call.started, call.answered, "
        "recording.ready, call.ended) from the Edesy voice infrastructure."
    ),
)
async def edesy_call_event_webhook(
    event: EdesyWebhookEvent,
    request: Request,
    x_edesy_signature: Optional[str] = Header(None),
) -> Dict[str, Any]:
    # Validate secret if configured
    if EDESY_WEBHOOK_SECRET and x_edesy_signature:
        if x_edesy_signature != EDESY_WEBHOOK_SECRET:
            logger.warning("Invalid webhook signature received for call %s", event.call_sid)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Edesy webhook signature",
            )

    controller = get_controller(request)
    logger.info("Edesy lifecycle event '%s' received for call SID %s", event.event_type, event.call_sid)

    if event.event_type == "call.initiated":
        controller.start_call(
            session_id=event.call_sid,
            caller_phone=event.from_number,
        )
    elif event.event_type == "call.ended":
        controller.end_call(session_id=event.call_sid)

    return {
        "status": "received",
        "call_sid": event.call_sid,
        "event_type": event.event_type,
    }


@router.post(
    "/tool",
    response_model=EdesyToolResponse,
    summary="Edesy Mid-Conversation AI Tool Endpoint",
    description=(
        "Synchronous HTTP tool endpoint invoked mid-call by Edesy's Conversational AI "
        "agent when caller speech is transcribed and needs Dhwani-Sanjeevani emergency triage."
    ),
)
async def edesy_conversation_tool(
    payload: EdesyToolRequest,
    request: Request,
) -> EdesyToolResponse:
    controller = get_controller(request)

    # Resolve utterance from either transcript or message field
    utterance = payload.transcript or payload.message or ""

    result = await controller.process_utterance(
        session_id=payload.call_sid,
        transcript=utterance,
        caller_phone=payload.caller_phone,
    )

    should_end = result.get("next_action") == "END_CALL"

    return EdesyToolResponse(
        response_text=result["response_text"],
        next_action=result["next_action"],
        end_call=should_end,
        conversation_id=result.get("conversation_id"),
        case_id=result.get("case_id"),
        language=result.get("language", "hindi"),
    )

