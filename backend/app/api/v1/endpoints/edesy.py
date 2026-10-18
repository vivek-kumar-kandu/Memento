import logging
import time
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.common import Channel
from app.schemas.assistant import AssistantMessageRequest
from app.schemas.edesy import EdesyToolRequest, EdesyToolResponse, EdesyWebhookEvent
from app.services.assistant_service import assistant_service
from app.services.speech_service import SpeechAdapter

logger = logging.getLogger("backend.edesy_router")

router = APIRouter(prefix="/edesy", tags=["Edesy IVR Provider"])


class CallSessionState:
    def __init__(self, session_id: str, caller_phone: Optional[str] = None):
        self.session_id = session_id
        self.caller_phone = caller_phone
        self.conversation_id: Optional[str] = None
        self.case_id: Optional[str] = None
        self.language: str = "hindi"
        self.no_input_count: int = 0
        self.turn_count: int = 0
        self.updated_at: float = time.time()


# In-memory session cache for active Edesy telephony calls
_CALL_SESSIONS: Dict[str, CallSessionState] = {}


def _get_or_create_session(session_id: str, caller_phone: Optional[str] = None) -> CallSessionState:
    if session_id not in _CALL_SESSIONS:
        _CALL_SESSIONS[session_id] = CallSessionState(session_id, caller_phone)
    session = _CALL_SESSIONS[session_id]
    session.updated_at = time.time()
    if caller_phone and not session.caller_phone:
        session.caller_phone = caller_phone
    return session


@router.post(
    "/webhook",
    summary="Edesy Asynchronous Call Lifecycle Webhook",
    description="Receives asynchronous telephony events (call.initiated, call.answered, call.ended) from Edesy voice infrastructure.",
)
async def edesy_call_event_webhook(
    event: EdesyWebhookEvent,
    x_edesy_signature: Optional[str] = Header(None),
) -> Dict[str, Any]:
    logger.info("Edesy lifecycle event '%s' received for call SID %s", event.event_type, event.call_sid)

    session = _get_or_create_session(event.call_sid, event.from_number)

    if event.event_type == "call.ended":
        _CALL_SESSIONS.pop(event.call_sid, None)

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
    db: AsyncSession = Depends(get_db),
) -> EdesyToolResponse:
    session = _get_or_create_session(payload.call_sid, payload.caller_phone)

    # 1. Resolve speech utterance
    utterance = (payload.transcript or payload.message or "").strip()

    # 2. Handle silence / empty input
    if not utterance:
        session.no_input_count += 1
        if session.no_input_count <= 2:
            prompt = SpeechAdapter.get_silence_retry_prompt(session.no_input_count, session.language)
            return EdesyToolResponse(
                response_text=SpeechAdapter.sanitize_for_tts(prompt),
                next_action="CONTINUE",
                end_call=False,
                conversation_id=session.conversation_id,
                case_id=session.case_id,
                language=session.language,
            )
        else:
            escalation = SpeechAdapter.get_escalation_prompt(session.language)
            return EdesyToolResponse(
                response_text=SpeechAdapter.sanitize_for_tts(escalation),
                next_action="ESCALATE_HUMAN",
                end_call=False,
                conversation_id=session.conversation_id,
                case_id=session.case_id,
                language=session.language,
            )

    # Reset silence counter and detect language
    session.no_input_count = 0
    session.turn_count += 1
    session.language = SpeechAdapter.detect_language(utterance, current_language=session.language)

    # 3. Handle explicit operator request
    lower_text = utterance.lower()
    has_emergency_terms = any(
        kw in lower_text
        for kw in [
            "saanp", "snake", "bite", "kaat", "katlas", "dhas", "wound", "field",
            "dard", "village", "hospital", "patient", "sujan", "vomit", "poison",
            "kaha", "kahan", "madad"
        ]
    )
    is_explicit_transfer = any(
        kw in lower_text for kw in ["operator", "human agent", "insaan se baat", "baat karao", "human please"]
    )
    if is_explicit_transfer and not has_emergency_terms:
        escalation = SpeechAdapter.get_escalation_prompt(session.language)
        return EdesyToolResponse(
            response_text=SpeechAdapter.sanitize_for_tts(escalation),
            next_action="ESCALATE_HUMAN",
            end_call=False,
            conversation_id=session.conversation_id,
            case_id=session.case_id,
            language=session.language,
        )

    # 4. Route to Universal Assistant Service
    assistant_req = AssistantMessageRequest(
        message=utterance,
        channel=Channel.IVR,
        conversation_id=session.conversation_id,
        caller_phone=session.caller_phone,
    )

    result = await assistant_service.handle_message(assistant_req, db)

    # Update session identifiers
    if result.conversation_id:
        session.conversation_id = result.conversation_id
    if result.case_id:
        session.case_id = result.case_id

    # 5. Format and sanitize TTS response for Edesy IVR
    localized_speech = SpeechAdapter.format_edesy_response(
        result=result,
        language=session.language,
    )
    sanitized_speech = SpeechAdapter.sanitize_for_tts(localized_speech)

    should_end = result.next_action == "END_CALL"

    return EdesyToolResponse(
        response_text=sanitized_speech,
        next_action=result.next_action,
        end_call=should_end,
        conversation_id=session.conversation_id,
        case_id=session.case_id,
        language=session.language,
    )
