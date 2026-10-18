import logging
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import Channel
from app.schemas.assistant import AssistantMessageRequest
from app.schemas.edesy import EdesyToolRequest, EdesyToolResponse, EdesyWebhookEvent
from app.services.assistant_service import assistant_service
from app.services.speech_service import SpeechAdapter

logger = logging.getLogger("backend.edesy_router")

router = APIRouter(prefix="/edesy", tags=["Edesy IVR Provider"])


# ---------------------------------------------------------------------------
# Flow state machine definition
# ---------------------------------------------------------------------------

class FlowStep(str, Enum):
    ASK_SYMPTOM_1 = "ASK_SYMPTOM_1"
    ASK_SYMPTOM_2 = "ASK_SYMPTOM_2"
    ASK_SYMPTOM_3 = "ASK_SYMPTOM_3"
    COLLECT_LOCATION = "COLLECT_LOCATION"
    DONE = "DONE"


# Three symptom screening questions — plain Hinglish, one per turn
_Q1 = (
    "Patient ki palkein jhuk rahi hain, aankhein khuli rakhne mein dikkat ho rahi hai, "
    "ya dhundhla ya double dikh raha hai?"
)
_Q2 = (
    "Kya patient ko bolne ya nigalne mein dikkat, awaaz badalne, saans lene mein takleef, "
    "ya bahut kamzori ho rahi hai?"
)
_Q3 = (
    "Kya bite wali jagah se khoon ruk nahi raha, naak ya masoodon se khoon aa raha hai, "
    "peshab ya ulti mein khoon hai, ya sujan tezi se badh rahi hai?"
)
_LOCATION_QUESTION = "Apna gaon ya mohalla, district aur paas ka koi landmark bataiye."

# Immediate-danger keywords — if detected, skip remaining symptom Qs and escalate
_EMERGENCY_NOW_KEYWORDS = [
    "saans nahi", "saans band", "unconscious", "behosh", "nahi le pa", "nahi nigl",
    "breathing", "paralysis", "laqwa", "baat nahi", "bol nahi", "nigl nahi",
    "khoon band nahi", "khoon ruk nahi", "bahut khoon", "blood not stopping",
]

_EMERGENCY_IMMEDIATE_ADVICE = (
    "Yeh bahut serious symptoms hain. Abhi 108 ya 112 par call karen. "
    "Patient ko bilkul shant aur still rakhein. Bite wali jagah ko heart ke barabar level par rakhein. "
    "Koi chira na lagaein, zehar na choosein."
)


# ---------------------------------------------------------------------------
# In-memory call session
# ---------------------------------------------------------------------------

class CallSessionState:
    """Per-call state persisted in memory for the lifetime of the Edesy call."""

    def __init__(self, session_id: str, caller_phone: Optional[str] = None):
        self.session_id: str = session_id
        self.caller_phone: Optional[str] = caller_phone
        # Internal backend IDs — NEVER put in response_text
        self.conversation_id: Optional[str] = None
        self.case_id: Optional[str] = None
        self.language: str = "hinglish"
        self.no_input_count: int = 0
        self.turn_count: int = 0
        self.updated_at: float = time.time()
        # Symptom flow state
        self.flow_step: FlowStep = FlowStep.ASK_SYMPTOM_1
        self.symptom_answers: List[str] = []
        # If caller volunteers location before COLLECT_LOCATION, cache it here
        self.collected_location: Optional[str] = None
        # Whether we already asked for clarification once on the current question
        self.current_q_retry: bool = False


# In-memory session registry, keyed by Edesy call_sid
_CALL_SESSIONS: Dict[str, CallSessionState] = {}


def _get_or_create_session(
    session_id: str, caller_phone: Optional[str] = None
) -> CallSessionState:
    if session_id not in _CALL_SESSIONS:
        _CALL_SESSIONS[session_id] = CallSessionState(session_id, caller_phone)
    session = _CALL_SESSIONS[session_id]
    session.updated_at = time.time()
    if caller_phone and not session.caller_phone:
        session.caller_phone = caller_phone
    return session


# ---------------------------------------------------------------------------
# Helper: strip internal IDs from any text before it reaches TTS
# ---------------------------------------------------------------------------

def _strip_case_id(text: str) -> str:
    """Remove Case ID, conversation ID, and record ID patterns from spoken text."""
    # "Case ID: DS-2026-XXXXXX" with optional parens/period
    text = re.sub(
        r"\(?Case ID:\s*[A-Za-z0-9\-]+\)?\.?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # "conversation_id: ..." or "conversation id: ..."
    text = re.sub(
        r"\(?conversation[_ ]?id:\s*[A-Za-z0-9\-]+\)?\.?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Standalone DS-YYYY-XXXXXX tokens
    text = re.sub(r"\bDS-\d{4}-[A-Z0-9]+\b", "", text)
    # Full UUID patterns
    text = re.sub(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Collapse residual whitespace / punctuation artefacts
    text = re.sub(r"\s{2,}", " ", text).strip(" .,;-")
    return text


def _build_tts(text: str) -> str:
    """Strip IDs then sanitize for TTS."""
    return SpeechAdapter.sanitize_for_tts(_strip_case_id(text))


def _safe_response(
    text: str,
    next_action: str,
    session: CallSessionState,
    end_call: bool = False,
) -> EdesyToolResponse:
    return EdesyToolResponse(
        response_text=_build_tts(text),
        next_action=next_action,
        end_call=end_call,
        conversation_id=session.conversation_id,
        case_id=session.case_id,
        language=session.language,
    )


def _is_emergency_now(utterance: str) -> bool:
    """True if caller describes an immediate life-threatening sign."""
    lower = utterance.lower()
    return any(kw in lower for kw in _EMERGENCY_NOW_KEYWORDS)


def _looks_like_location(text: str) -> bool:
    """Heuristic: does this utterance contain location-like tokens?"""
    lower = text.lower()
    location_kw = [
        "village", "gaon", "mohalla", "district", "block", "near",
        "paas", "mein hain", "tehsil", "taluk", "nagar",
    ]
    return any(kw in lower for kw in location_kw) and len(text.split()) >= 3


# ---------------------------------------------------------------------------
# Facility results → short spoken text (no IDs, no unverified claims)
# ---------------------------------------------------------------------------

def _format_facilities_for_voice(nearby_items: Any) -> str:
    """
    Build a short, accurate spoken string from real facility records.
    Never invents names, distances, or capabilities.
    """
    if not nearby_items:
        return (
            "Aapke location ke 30 km mein koi PHC ya CHC nahi mila. "
            "Abhi 108 emergency ambulance ko call karen aur nearest government hospital ke liye poochhen."
        )

    parts: List[str] = []
    for i, fac in enumerate(nearby_items[:3]):
        # Support both ORM objects (attribute access) and dicts
        name = getattr(fac, "facility_name", None) or (fac.get("facility_name") if isinstance(fac, dict) else None) or "PHC/CHC"
        dist_km = getattr(fac, "distance_km", None) or (fac.get("distance_km") if isinstance(fac, dict) else None)
        district = getattr(fac, "district_name", None) or (fac.get("district_name") if isinstance(fac, dict) else None) or ""
        ftype = getattr(fac, "facility_type", None) or (fac.get("facility_type") if isinstance(fac, dict) else None) or ""

        dist_str = f"{dist_km:.1f} km" if dist_km is not None else "paas mein"
        line = f"{i + 1}. {name}"
        if district:
            line += f", {district}"
        line += f" — {dist_str}"
        if ftype:
            line += f" ({ftype})"
        parts.append(line)

    header = f"Aapke paas {len(parts)} facility mili:"
    detail = " | ".join(parts)
    footer = (
        "108 ambulance se patient ko turant lejayein. "
        "ASV stock ki guarantee nahi hai, pahunchne se pehle call karke confirm karen."
    )
    return f"{header} {detail}. {footer}"


# ---------------------------------------------------------------------------
# Webhook endpoint (call lifecycle events)
# ---------------------------------------------------------------------------

@router.post(
    "/webhook",
    summary="Edesy Asynchronous Call Lifecycle Webhook",
    description=(
        "Receives asynchronous telephony events (call.initiated, call.answered, call.ended) "
        "from Edesy voice infrastructure."
    ),
)
async def edesy_call_event_webhook(
    event: EdesyWebhookEvent,
    x_edesy_signature: Optional[str] = Header(None),
) -> Dict[str, Any]:
    logger.info(
        "Edesy lifecycle event '%s' received for call SID %s",
        event.event_type,
        event.call_sid,
    )
    _get_or_create_session(event.call_sid, event.from_number)

    if event.event_type == "call.ended":
        _CALL_SESSIONS.pop(event.call_sid, None)

    return {
        "status": "received",
        "call_sid": event.call_sid,
        "event_type": event.event_type,
    }


# ---------------------------------------------------------------------------
# Main tool endpoint — state machine
# ---------------------------------------------------------------------------

@router.post(
    "/tool",
    response_model=EdesyToolResponse,
    summary="Edesy Mid-Conversation AI Tool Endpoint",
    description=(
        "Synchronous HTTP tool endpoint invoked mid-call by Edesy's Conversational AI "
        "agent. Implements a strict 3-symptom → location → real PHC/CHC flow. "
        "Case IDs are never included in response_text."
    ),
)
async def edesy_conversation_tool(
    payload: EdesyToolRequest,
    db: AsyncSession = Depends(get_db),
) -> EdesyToolResponse:
    session = _get_or_create_session(payload.call_sid, payload.caller_phone)

    # ── 1. Resolve utterance ──────────────────────────────────────────────
    utterance = (payload.transcript or payload.message or "").strip()

    # ── 2. Silence / empty input ──────────────────────────────────────────
    if not utterance:
        session.no_input_count += 1
        if session.no_input_count <= 2:
            # Repeat the current question instead of a generic prompt
            current_q = {
                FlowStep.ASK_SYMPTOM_1: _Q1,
                FlowStep.ASK_SYMPTOM_2: _Q2,
                FlowStep.ASK_SYMPTOM_3: _Q3,
                FlowStep.COLLECT_LOCATION: _LOCATION_QUESTION,
            }.get(session.flow_step, _Q1)
            retry_prefix = "Kripya dobara bataiye — " if session.no_input_count == 2 else ""
            return _safe_response(f"{retry_prefix}{current_q}", "CONTINUE", session)
        else:
            escalation = SpeechAdapter.get_escalation_prompt(session.language)
            return _safe_response(escalation, "ESCALATE_HUMAN", session)

    # Reset silence counter, update language, increment turn
    session.no_input_count = 0
    session.turn_count += 1
    session.language = SpeechAdapter.detect_language(utterance, current_language=session.language)

    # ── 3. Explicit operator escalation (only when no emergency context) ──
    lower_text = utterance.lower()
    has_emergency_terms = any(
        kw in lower_text
        for kw in [
            "saanp", "snake", "bite", "kaat", "katlas", "dhas", "wound", "field",
            "dard", "village", "hospital", "patient", "sujan", "vomit", "poison",
            "kaha", "kahan", "madad", "saans", "khoon",
        ]
    )
    is_explicit_transfer = any(
        kw in lower_text
        for kw in ["operator", "human agent", "insaan se baat", "baat karao", "human please"]
    )
    if is_explicit_transfer and not has_emergency_terms:
        escalation = SpeechAdapter.get_escalation_prompt(session.language)
        return _safe_response(escalation, "ESCALATE_HUMAN", session)

    # ── 4. Emergency-now detection — skip remaining symptom Qs ───────────
    if _is_emergency_now(utterance) and session.flow_step in (
        FlowStep.ASK_SYMPTOM_1,
        FlowStep.ASK_SYMPTOM_2,
        FlowStep.ASK_SYMPTOM_3,
    ):
        session.symptom_answers.append(f"[EMERGENCY_NOW] {utterance[:100]}")
        session.flow_step = FlowStep.COLLECT_LOCATION
        advice = f"{_EMERGENCY_IMMEDIATE_ADVICE} Saath mein bataiye: {_LOCATION_QUESTION}"
        return _safe_response(advice, "COLLECT_LOCATION", session)

    # ── 5. Opportunistic location caching during symptom questions ────────
    if session.flow_step in (
        FlowStep.ASK_SYMPTOM_1,
        FlowStep.ASK_SYMPTOM_2,
        FlowStep.ASK_SYMPTOM_3,
    ) and _looks_like_location(utterance):
        session.collected_location = utterance

    # ── 6. State machine ─────────────────────────────────────────────────

    if session.flow_step == FlowStep.ASK_SYMPTOM_1:
        session.symptom_answers.append(utterance[:100])
        session.flow_step = FlowStep.ASK_SYMPTOM_2
        session.current_q_retry = False
        return _safe_response(_Q2, "CONTINUE", session)

    elif session.flow_step == FlowStep.ASK_SYMPTOM_2:
        session.symptom_answers.append(utterance[:100])
        session.flow_step = FlowStep.ASK_SYMPTOM_3
        session.current_q_retry = False
        return _safe_response(_Q3, "CONTINUE", session)

    elif session.flow_step == FlowStep.ASK_SYMPTOM_3:
        session.symptom_answers.append(utterance[:100])
        session.flow_step = FlowStep.COLLECT_LOCATION
        session.current_q_retry = False
        # If caller already gave location during symptom turns, use it now
        if session.collected_location:
            session.flow_step = FlowStep.DONE
            return await _do_facility_lookup(session.collected_location, session, db)
        return _safe_response(_LOCATION_QUESTION, "COLLECT_LOCATION", session)

    elif session.flow_step == FlowStep.COLLECT_LOCATION:
        # Ask for clarification once if the answer is too short / unintelligible
        if len(utterance.split()) < 2 and not session.current_q_retry:
            session.current_q_retry = True
            clarification = (
                "Kripya apna gaon, mohalla ya nearest town thoda clearly bataiye "
                "taaki hum nearest PHC/CHC dhundh sakein."
            )
            return _safe_response(clarification, "COLLECT_LOCATION", session)

        session.flow_step = FlowStep.DONE
        return await _do_facility_lookup(utterance, session, db)

    else:
        # FlowStep.DONE — additional turns after flow is complete
        return _safe_response(
            "Sabse zaruri hai: 108 ambulance turant bulaiye aur patient ko still rakhein. "
            "Kya aur madad chahiye?",
            "CONTINUE",
            session,
        )


# ---------------------------------------------------------------------------
# Facility lookup — calls assistant_service for real DB results
# ---------------------------------------------------------------------------

async def _do_facility_lookup(
    location_text: str,
    session: CallSessionState,
    db: AsyncSession,
) -> EdesyToolResponse:
    """
    Delegates to assistant_service to:
    - Persist/link the emergency case record internally
    - Run the BallTree spatial search against the real facility DB
    - Return actual nearby PHC/CHC records

    The backend's response_text is intentionally DISCARDED — we build our own
    short, ID-free, voice-safe spoken text from the nearby_facilities list.
    """
    try:
        assistant_req = AssistantMessageRequest(
            message=location_text,
            channel=Channel.IVR,
            conversation_id=session.conversation_id,
            caller_phone=session.caller_phone,
        )
        result = await assistant_service.handle_message(assistant_req, db)

        # Store IDs internally — they must NOT appear in response_text
        if result.conversation_id:
            session.conversation_id = result.conversation_id
        if result.case_id:
            session.case_id = result.case_id

        # Location unresolvable → ask for clarification
        if result.next_action == "COLLECT_LOCATION" and not result.nearby_facilities:
            session.flow_step = FlowStep.COLLECT_LOCATION
            clarification = (
                "Location clearly nahi aayi. Kripya apna nearest block, tehsil ya bada shahar bataiye "
                "taaki nearest PHC/CHC dhundha ja sake."
            )
            return _safe_response(clarification, "COLLECT_LOCATION", session)

        spoken = _format_facilities_for_voice(result.nearby_facilities)
        action = result.next_action or "DISPATCH_OR_TRANSPORT"
        return _safe_response(spoken, action, session)

    except Exception as exc:
        logger.error(
            "Facility lookup failed for session %s: %s",
            session.session_id,
            exc,
            exc_info=True,
        )
        fallback = (
            "Backend se facility data nahi aa saka. "
            "Abhi 108 emergency ambulance ko call karen aur nearest government hospital jayen."
        )
        return _safe_response(fallback, "ESCALATE_HUMAN", session)
