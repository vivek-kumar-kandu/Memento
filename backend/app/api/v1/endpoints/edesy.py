import logging
import re
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import get_db
from app.db.models.conversation import ConversationSession
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
# Persistence: database-backed session state via ConversationSession
# ---------------------------------------------------------------------------

# Deprecated in-memory dictionary maintained only for legacy inspection/clearing compatibility.
# The database table `conversation_sessions` is the SOLE authoritative source of truth.
_CALL_SESSIONS: Dict[str, Any] = {}


def _derive_session_id(call_sid: str) -> str:
    """
    Map call_sid to a stable string fitting within ConversationSession.id (String(36)).
    If len(call_sid) <= 36, use call_sid directly for traceability and human readability.
    If len(call_sid) > 36, generate a deterministic UUID5 using NAMESPACE_URL.
    """
    if len(call_sid) <= 36:
        return call_sid
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"edesy:{call_sid}"))


async def _get_or_create_session(
    db: AsyncSession,
    call_sid: str,
    caller_phone: Optional[str] = None,
) -> ConversationSession:
    """
    Retrieve or initialize the durable database-backed ConversationSession for this call_sid.
    All state is stored in context_data JSON.
    """
    session_id = _derive_session_id(call_sid)
    stmt = select(ConversationSession).where(ConversationSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session is not None:
        # Update phone if newly provided
        if caller_phone:
            ctx = dict(session.context_data or {})
            if not ctx.get("caller_phone"):
                ctx["caller_phone"] = caller_phone
                session.context_data = ctx
                flag_modified(session, "context_data")
                await db.commit()
                await db.refresh(session)
        return session

    # Initialize new session in DB
    now = datetime.now(timezone.utc)
    init_context: Dict[str, Any] = {
        "call_sid": call_sid,
        "flow_step": FlowStep.ASK_SYMPTOM_1.value,
        "symptom_answers": [],
        "collected_location": None,
        "current_q_retry": False,
        "no_input_count": 0,
        "turn_count": 0,
        "language": "hinglish",
        "caller_phone": caller_phone,
        "case_id": None,
        "conversation_id": session_id,
        "updated_at": time.time(),
    }
    session = ConversationSession(
        id=session_id,
        channel=Channel.IVR.value,
        case_id=None,
        state="ACTIVE",
        context_data=init_context,
        last_message=None,
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
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
    conversation_id: Optional[str] = None,
    case_id: Optional[str] = None,
    language: str = "hinglish",
    end_call: bool = False,
) -> EdesyToolResponse:
    return EdesyToolResponse(
        response_text=_build_tts(text),
        next_action=next_action,
        end_call=end_call,
        conversation_id=conversation_id,
        case_id=case_id,
        language=language,
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
    db: AsyncSession = Depends(get_db),
    x_edesy_signature: Optional[str] = Header(None),
) -> Dict[str, Any]:
    logger.info(
        "Edesy lifecycle event '%s' received for call SID %s",
        event.event_type,
        event.call_sid,
    )
    session = await _get_or_create_session(db, event.call_sid, event.from_number)

    if event.event_type == "call.ended":
        session.state = "COMPLETED"
        session.updated_at = datetime.now(timezone.utc)
        ctx = dict(session.context_data or {})
        ctx["call_ended_at"] = time.time()
        session.context_data = ctx
        flag_modified(session, "context_data")
        await db.commit()

    return {
        "status": "received",
        "call_sid": event.call_sid,
        "event_type": event.event_type,
    }


# ---------------------------------------------------------------------------
# Main tool endpoint — durable database-backed state machine
# ---------------------------------------------------------------------------

@router.post(
    "/tool",
    response_model=EdesyToolResponse,
    summary="Edesy Mid-Conversation AI Tool Endpoint",
    description=(
        "Synchronous HTTP tool endpoint invoked mid-call by Edesy's Conversational AI "
        "agent. Implements a durable database-backed 3-symptom → location → real PHC/CHC flow. "
        "Case IDs are never included in response_text."
    ),
)
async def edesy_conversation_tool(
    payload: EdesyToolRequest,
    db: AsyncSession = Depends(get_db),
) -> EdesyToolResponse:
    # ── 0. Resolve stable call/session identifier ──────────────────────────
    raw_call_sid = (
        payload.call_sid
        or payload.call_id
        or payload.session_id
        or payload.conversation_id
    )
    if not raw_call_sid or not raw_call_sid.strip():
        logger.error(
            "Edesy tool request missing required call identifier: %s",
            payload.model_dump(),
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing required call identifier. The Edesy tool configuration must supply "
                "'call_sid' (or 'call_id' / 'session_id') so session state can be tracked."
            ),
        )
    call_sid = raw_call_sid.strip()
    session_id = _derive_session_id(call_sid)
    session_case_id: Optional[str] = None
    language: str = "hinglish"

    try:
        # Load or initialize durable session from the database
        session = await _get_or_create_session(db, call_sid, payload.caller_phone)
        session_id = session.id
        session_case_id = session.case_id
        context = dict(session.context_data or {})
        flow_step = FlowStep(context.get("flow_step", FlowStep.ASK_SYMPTOM_1.value))
        symptom_answers = list(context.get("symptom_answers", []))
        collected_location = context.get("collected_location")
        current_q_retry = context.get("current_q_retry", False)
        no_input_count = context.get("no_input_count", 0)
        turn_count = context.get("turn_count", 0)
        language = context.get("language", "hinglish")

        # ── 1. Resolve utterance ──────────────────────────────────────────
        utterance = (payload.transcript or payload.message or "").strip()

        # ── 2. Silence / empty input ──────────────────────────────────────
        if not utterance:
            no_input_count += 1
            context["no_input_count"] = no_input_count
            context["updated_at"] = time.time()
            session.context_data = context
            flag_modified(session, "context_data")
            await db.commit()
            await db.refresh(session)

            if no_input_count <= 2:
                current_q = {
                    FlowStep.ASK_SYMPTOM_1: _Q1,
                    FlowStep.ASK_SYMPTOM_2: _Q2,
                    FlowStep.ASK_SYMPTOM_3: _Q3,
                    FlowStep.COLLECT_LOCATION: _LOCATION_QUESTION,
                }.get(flow_step, _Q1)
                retry_prefix = "Kripya dobara bataiye — " if no_input_count == 2 else ""
                return _safe_response(
                    f"{retry_prefix}{current_q}",
                    "CONTINUE",
                    conversation_id=session.id,
                    case_id=session.case_id,
                    language=language,
                )
            else:
                escalation = SpeechAdapter.get_escalation_prompt(language)
                return _safe_response(
                    escalation,
                    "ESCALATE_HUMAN",
                    conversation_id=session.id,
                    case_id=session.case_id,
                    language=language,
                )

        # Reset silence counter, update language, increment turn count
        no_input_count = 0
        turn_count += 1
        language = SpeechAdapter.detect_language(utterance, current_language=language)
        context["no_input_count"] = 0
        context["turn_count"] = turn_count
        context["language"] = language
        session.last_message = utterance[:1000]

        # ── 3. Explicit operator escalation (only when no emergency context)
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
            session.state = "ESCALATED"
            context["updated_at"] = time.time()
            session.context_data = context
            flag_modified(session, "context_data")
            await db.commit()
            await db.refresh(session)
            escalation = SpeechAdapter.get_escalation_prompt(language)
            return _safe_response(
                escalation,
                "ESCALATE_HUMAN",
                conversation_id=session.id,
                case_id=session.case_id,
                language=language,
            )

        # ── 4. Emergency-now detection — skip remaining symptom Qs ───────
        if _is_emergency_now(utterance) and flow_step in (
            FlowStep.ASK_SYMPTOM_1,
            FlowStep.ASK_SYMPTOM_2,
            FlowStep.ASK_SYMPTOM_3,
        ):
            symptom_answers.append(f"[EMERGENCY_NOW] {utterance[:100]}")
            flow_step = FlowStep.COLLECT_LOCATION
            context["flow_step"] = flow_step.value
            context["symptom_answers"] = symptom_answers
            context["updated_at"] = time.time()
            session.context_data = context
            flag_modified(session, "context_data")
            await db.commit()
            await db.refresh(session)
            advice = f"{_EMERGENCY_IMMEDIATE_ADVICE} Saath mein bataiye: {_LOCATION_QUESTION}"
            return _safe_response(
                advice,
                "COLLECT_LOCATION",
                conversation_id=session.id,
                case_id=session.case_id,
                language=language,
            )

        # ── 5. Opportunistic location caching during symptom questions ────
        if flow_step in (
            FlowStep.ASK_SYMPTOM_1,
            FlowStep.ASK_SYMPTOM_2,
            FlowStep.ASK_SYMPTOM_3,
        ) and _looks_like_location(utterance):
            collected_location = utterance
            context["collected_location"] = collected_location

        # ── 6. State machine ─────────────────────────────────────────────

        if flow_step == FlowStep.ASK_SYMPTOM_1:
            symptom_answers.append(utterance[:100])
            flow_step = FlowStep.ASK_SYMPTOM_2
            current_q_retry = False
            context["flow_step"] = flow_step.value
            context["symptom_answers"] = symptom_answers
            context["current_q_retry"] = current_q_retry
            context["updated_at"] = time.time()
            session.context_data = context
            flag_modified(session, "context_data")
            await db.commit()
            await db.refresh(session)
            return _safe_response(
                _Q2,
                "CONTINUE",
                conversation_id=session.id,
                case_id=session.case_id,
                language=language,
            )

        elif flow_step == FlowStep.ASK_SYMPTOM_2:
            symptom_answers.append(utterance[:100])
            flow_step = FlowStep.ASK_SYMPTOM_3
            current_q_retry = False
            context["flow_step"] = flow_step.value
            context["symptom_answers"] = symptom_answers
            context["current_q_retry"] = current_q_retry
            context["updated_at"] = time.time()
            session.context_data = context
            flag_modified(session, "context_data")
            await db.commit()
            await db.refresh(session)
            return _safe_response(
                _Q3,
                "CONTINUE",
                conversation_id=session.id,
                case_id=session.case_id,
                language=language,
            )

        elif flow_step == FlowStep.ASK_SYMPTOM_3:
            symptom_answers.append(utterance[:100])
            flow_step = FlowStep.COLLECT_LOCATION
            current_q_retry = False
            context["flow_step"] = flow_step.value
            context["symptom_answers"] = symptom_answers
            context["current_q_retry"] = current_q_retry
            context["updated_at"] = time.time()
            session.context_data = context
            flag_modified(session, "context_data")
            await db.commit()
            await db.refresh(session)

            # If caller already gave location during symptom turns, use it now
            if collected_location:
                context["flow_step"] = FlowStep.DONE.value
                session.context_data = context
                flag_modified(session, "context_data")
                await db.commit()
                await db.refresh(session)
                return await _do_facility_lookup(collected_location, session, db, language=language)
            return _safe_response(
                _LOCATION_QUESTION,
                "COLLECT_LOCATION",
                conversation_id=session.id,
                case_id=session.case_id,
                language=language,
            )

        elif flow_step == FlowStep.COLLECT_LOCATION:
            # Ask for clarification once if the answer is too short / unintelligible
            if len(utterance.split()) < 2 and not current_q_retry:
                current_q_retry = True
                context["current_q_retry"] = current_q_retry
                context["updated_at"] = time.time()
                session.context_data = context
                flag_modified(session, "context_data")
                await db.commit()
                await db.refresh(session)
                clarification = (
                    "Kripya apna gaon, mohalla ya nearest town thoda clearly bataiye "
                    "taaki hum nearest PHC/CHC dhundh sakein."
                )
                return _safe_response(
                    clarification,
                    "COLLECT_LOCATION",
                    conversation_id=session.id,
                    case_id=session.case_id,
                    language=language,
                )

            context["flow_step"] = FlowStep.DONE.value
            context["updated_at"] = time.time()
            session.context_data = context
            flag_modified(session, "context_data")
            await db.commit()
            await db.refresh(session)
            return await _do_facility_lookup(utterance, session, db, language=language)

        else:
            # FlowStep.DONE — additional turns after flow is complete
            context["updated_at"] = time.time()
            session.context_data = context
            flag_modified(session, "context_data")
            await db.commit()
            await db.refresh(session)
            return _safe_response(
                "Sabse zaruri hai: 108 ambulance turant bulaiye aur patient ko still rakhein. "
                "Kya aur madad chahiye?",
                "CONTINUE",
                conversation_id=session.id,
                case_id=session.case_id,
                language=language,
            )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Database/transaction failure in edesy_conversation_tool for call_sid %s: %s",
            call_sid,
            exc,
            exc_info=True,
        )
        try:
            await db.rollback()
        except Exception:
            pass
        return _safe_response(
            "Backend se sampark nahi ho saka. Kripya turant 108 emergency ambulance ko call karen.",
            "ESCALATE_HUMAN",
            conversation_id=session_id,
            case_id=session_case_id,
            language=language,
        )


# ---------------------------------------------------------------------------
# Facility lookup — calls assistant_service for real DB results
# ---------------------------------------------------------------------------

async def _do_facility_lookup(
    location_text: str,
    session: ConversationSession,
    db: AsyncSession,
    language: Optional[str] = None,
) -> EdesyToolResponse:
    """
    Delegates to assistant_service to:
    - Persist/link the emergency case record internally
    - Run the BallTree spatial search against the real facility DB
    - Return actual nearby PHC/CHC records

    The backend's response_text is intentionally DISCARDED — we build our own
    short, ID-free, voice-safe spoken text from the nearby_facilities list.
    """
    session_id = session.id
    current_case_id = session.case_id
    lang = language or "hinglish"

    try:
        ctx = dict(session.context_data or {})
        assistant_req = AssistantMessageRequest(
            message=location_text,
            channel=Channel.IVR,
            conversation_id=session.id,
            caller_phone=ctx.get("caller_phone"),
        )
        result = await assistant_service.handle_message(assistant_req, db)

        # Refresh session from DB after assistant_service commit
        await db.refresh(session)
        ctx = dict(session.context_data or {})

        # Store IDs internally — they must NOT appear in response_text
        if result.case_id:
            session.case_id = result.case_id
            ctx["case_id"] = result.case_id
            current_case_id = result.case_id
        if result.conversation_id:
            ctx["conversation_id"] = result.conversation_id
            session_id = result.conversation_id

        # Location unresolvable → ask for clarification
        if result.next_action == "COLLECT_LOCATION" and not result.nearby_facilities:
            ctx["flow_step"] = FlowStep.COLLECT_LOCATION.value
            ctx["updated_at"] = time.time()
            session.context_data = ctx
            flag_modified(session, "context_data")
            await db.commit()
            await db.refresh(session)
            clarification = (
                "Location clearly nahi aayi. Kripya apna nearest block, tehsil ya bada shahar bataiye "
                "taaki nearest PHC/CHC dhundha ja sake."
            )
            return _safe_response(
                clarification,
                "COLLECT_LOCATION",
                conversation_id=session_id,
                case_id=current_case_id,
                language=lang,
            )

        ctx["flow_step"] = FlowStep.DONE.value
        ctx["updated_at"] = time.time()
        session.context_data = ctx
        flag_modified(session, "context_data")
        await db.commit()
        await db.refresh(session)

        spoken = _format_facilities_for_voice(result.nearby_facilities)
        action = result.next_action or "DISPATCH_OR_TRANSPORT"
        return _safe_response(
            spoken,
            action,
            conversation_id=session_id,
            case_id=current_case_id,
            language=lang,
        )

    except Exception as exc:
        logger.error(
            "Facility lookup failed for session %s: %s",
            session_id,
            exc,
            exc_info=True,
        )
        try:
            await db.rollback()
        except Exception:
            pass
        fallback = (
            "Backend se facility data nahi aa saka. "
            "Abhi 108 emergency ambulance ko call karen aur nearest government hospital jayen."
        )
        return _safe_response(
            fallback,
            "ESCALATE_HUMAN",
            conversation_id=session_id,
            case_id=current_case_id,
            language=lang,
        )
