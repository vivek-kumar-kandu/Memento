import logging
import time
from typing import Any, Dict, Optional


from pydantic import BaseModel, Field

try:
    from backend_client import BackendClient, AssistantMessageResponse
    from speech import SpeechAdapter
    from config import DEFAULT_LANGUAGE, MAX_NO_INPUT_RETRIES
except ImportError:
    from .backend_client import BackendClient, AssistantMessageResponse
    from .speech import SpeechAdapter
    from .config import DEFAULT_LANGUAGE, MAX_NO_INPUT_RETRIES

logger = logging.getLogger("ivr.conversation")


class CallSession(BaseModel):
    session_id: str = Field(..., description="Unique telephony call SID or session ID")
    caller_phone: Optional[str] = Field(default=None, description="Caller phone number")
    conversation_id: Optional[str] = Field(default=None, description="Backend conversational state ID")
    case_id: Optional[str] = Field(default=None, description="Backend emergency case ID")
    language: str = Field(default="hindi", description="Call language code")

    turn_count: int = Field(default=0, description="Total turns completed")
    no_input_count: int = Field(default=0, description="Consecutive silence/empty input turns")
    is_active: bool = Field(default=True, description="Call active status")
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class SessionStore:
    """In-memory session registry for active IVR calls."""

    def __init__(self):
        self._sessions: Dict[str, CallSession] = {}

    def get(self, session_id: str) -> Optional[CallSession]:
        return self._sessions.get(session_id)

    def create(
        self,
        session_id: str,
        caller_phone: Optional[str] = None,
        language: Optional[str] = None,
    ) -> CallSession:
        session = CallSession(
            session_id=session_id,
            caller_phone=caller_phone,
            language=language or DEFAULT_LANGUAGE,
        )
        self._sessions[session_id] = session
        return session

    def update(self, session: CallSession) -> None:
        session.updated_at = time.time()
        self._sessions[session.session_id] = session

    def remove(self, session_id: str) -> Optional[CallSession]:
        return self._sessions.pop(session_id, None)

    def clear(self) -> None:
        self._sessions.clear()


class ConversationController:
    """Manages the full end-to-end IVR conversation lifecycle."""

    def __init__(
        self,
        backend_client: Optional[BackendClient] = None,
        session_store: Optional[SessionStore] = None,
    ):
        self.backend_client = backend_client or BackendClient()
        self.sessions = session_store or SessionStore()

    def start_call(
        self,
        session_id: str,
        caller_phone: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handles inbound call initiation and returns initial greeting."""
        session = self.sessions.create(session_id, caller_phone, language)
        greeting = SpeechAdapter.get_greeting(session.language)
        return {
            "session_id": session.session_id,
            "response_text": greeting,
            "next_action": "CONTINUE",
            "conversation_id": session.conversation_id,
            "case_id": session.case_id,
            "language": session.language,
        }

    async def process_utterance(
        self,
        session_id: str,
        transcript: Optional[str],
        caller_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes a caller utterance: handles empty input/retries,
        queries backend assistant, and formats safe response.
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.info("Session %s not found. Creating on the fly.", session_id)
            session = self.sessions.create(session_id, caller_phone)

        # Check for silence or empty transcript
        clean_text = (transcript or "").strip()
        if not clean_text:
            session.no_input_count += 1
            self.sessions.update(session)

            if session.no_input_count <= MAX_NO_INPUT_RETRIES:
                retry_prompt = SpeechAdapter.get_silence_retry_prompt(
                    session.no_input_count, session.language
                )
                return {
                    "session_id": session.session_id,
                    "response_text": retry_prompt,
                    "next_action": "CONTINUE",
                    "conversation_id": session.conversation_id,
                    "case_id": session.case_id,
                    "is_fallback": False,
                }
            else:
                # Repeated silence -> escalate to human support
                escalation_text = SpeechAdapter.get_escalation_prompt(session.language)
                return {
                    "session_id": session.session_id,
                    "response_text": escalation_text,
                    "next_action": "ESCALATE_HUMAN",
                    "conversation_id": session.conversation_id,
                    "case_id": session.case_id,
                    "is_fallback": True,
                }

        # Reset silence counter on receiving valid speech
        session.no_input_count = 0
        session.turn_count += 1

        # Detect and update language style (Hindi, Hinglish, Bhojpuri)
        session.language = SpeechAdapter.detect_language(
            text=clean_text,
            current_language=session.language,
        )
        self.sessions.update(session)

        # Check for human escalation keywords
        lower_text = clean_text.lower()
        if any(kw in lower_text for kw in ["operator", "human", "help me", "doctor", "madad", "baat karao"]):
            session.is_active = True
            self.sessions.update(session)
            escalation_text = SpeechAdapter.get_escalation_prompt(session.language)
            return {
                "session_id": session.session_id,
                "response_text": escalation_text,
                "next_action": "ESCALATE_HUMAN",
                "conversation_id": session.conversation_id,
                "case_id": session.case_id,
                "language": session.language,
                "is_fallback": False,
            }

        # Send to FastAPI Backend
        backend_resp: AssistantMessageResponse = await self.backend_client.send_message(
            message=clean_text,
            conversation_id=session.conversation_id,
            case_id=session.case_id,
            caller_phone=session.caller_phone or caller_phone,
            language=session.language,
        )

        # Preserve and update session state
        session.conversation_id = backend_resp.conversation_id
        if backend_resp.case_id:
            session.case_id = backend_resp.case_id
        self.sessions.update(session)

        # Localize response text to caller's language style
        localized_text = SpeechAdapter.localize_response(
            response_text=backend_resp.response_text,
            language=session.language,
            next_action=backend_resp.next_action,
        )
        spoken_text = SpeechAdapter.sanitize_for_tts(localized_text)

        # If facilities were returned and not already mentioned, append localized facility & ASV advice
        if backend_resp.facilities and len(backend_resp.facilities) > 0:
            top_facility = backend_resp.facilities[0]
            fac_name = top_facility.get("facility_name", "Primary Health Center")
            dist = top_facility.get("distance_km", 0.0)
            asv_stat = top_facility.get("asv_stock_status", "UNKNOWN")
            fac_speech = SpeechAdapter.format_asv_and_facility_speech(
                facility_name=fac_name,
                distance_km=dist,
                asv_status=asv_stat,
                language=session.language,
            )
            # Only append if not already in response text
            if fac_name.lower() not in spoken_text.lower():
                spoken_text = f"{spoken_text} {fac_speech}".strip()

        return {
            "session_id": session.session_id,
            "response_text": spoken_text,
            "next_action": backend_resp.next_action,
            "conversation_id": session.conversation_id,
            "case_id": session.case_id,
            "case_status": backend_resp.case_status,
            "facilities": backend_resp.facilities,
            "language": session.language,
            "is_fallback": backend_resp.is_fallback,
        }


    def end_call(self, session_id: str) -> Dict[str, Any]:
        """Terminates session and records call completion."""
        session = self.sessions.get(session_id)
        if session:
            session.is_active = False
            self.sessions.update(session)
            return {
                "session_id": session.session_id,
                "status": "COMPLETED",
                "turns": session.turn_count,
                "conversation_id": session.conversation_id,
                "case_id": session.case_id,
            }
        return {"session_id": session_id, "status": "NOT_FOUND"}
