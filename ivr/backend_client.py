import logging
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

try:
    from config import ASSISTANT_ENDPOINT, BACKEND_TIMEOUT_SECONDS, MAX_BACKEND_RETRIES
except ImportError:
    from .config import ASSISTANT_ENDPOINT, BACKEND_TIMEOUT_SECONDS, MAX_BACKEND_RETRIES

logger = logging.getLogger("ivr.backend_client")

# Clinician-reviewed emergency fallback guidance (never delays referral or invents diagnoses)
EMERGENCY_FALLBACK_TEXT = (
    "Emergency advisory: Keep the patient calm and completely still. "
    "Do not walk or move the bitten limb. Do not cut the wound, suck venom, "
    "or apply ice or a tourniquet. Proceed immediately to the nearest hospital "
    "or call 108 emergency ambulance service."
)


class AssistantMessageRequest(BaseModel):
    message: str = Field(..., description="Transcribed caller utterance")
    channel: str = Field(default="IVR", description="Channel identifier")
    conversation_id: Optional[str] = Field(default=None, description="Existing conversation ID")
    case_id: Optional[str] = Field(default=None, description="Associated emergency case ID")
    caller_phone: Optional[str] = Field(default=None, description="Caller telephone number")
    language: Optional[str] = Field(default="en", description="Language code")


class FacilityItem(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    state_name: str
    district_name: str
    distance_km: float
    asv_stock_status: str = "UNKNOWN"
    safety_disclaimer: Optional[str] = None


class AssistantMessageResponse(BaseModel):
    response_text: str = Field(..., description="Text response to be spoken to caller")
    next_action: str = Field(default="CONTINUE", description="Next conversation or triage action")
    conversation_id: str = Field(..., description="Unique conversation session ID")
    case_id: Optional[str] = Field(default=None, description="Emergency case ID")
    case_status: Optional[str] = Field(default=None, description="Current case status")
    facilities: Optional[List[Dict[str, Any]]] = Field(default=None, description="Nearby facilities")
    safety_disclaimer: Optional[str] = Field(default=None, description="Clinical/inventory disclaimer")
    is_fallback: bool = Field(default=False, description="True if generated locally due to backend failure")


class BackendClient:
    """Async HTTP Client for Dhwani-Sanjeevani FastAPI Backend."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.endpoint_url = endpoint_url or ASSISTANT_ENDPOINT
        self.timeout_seconds = timeout_seconds or BACKEND_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else MAX_BACKEND_RETRIES

    def _create_fallback_response(
        self, conversation_id: Optional[str], case_id: Optional[str]
    ) -> AssistantMessageResponse:
        """Returns safe clinician-approved emergency fallback response."""
        cid = conversation_id or "fallback-session"
        return AssistantMessageResponse(
            response_text=EMERGENCY_FALLBACK_TEXT,
            next_action="ESCALATE_HUMAN",
            conversation_id=cid,
            case_id=case_id,
            case_status="ESCALATED",
            facilities=None,
            safety_disclaimer="Direct emergency referral due to backend unavailability.",
            is_fallback=True,
        )

    async def send_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        case_id: Optional[str] = None,
        caller_phone: Optional[str] = None,
        language: str = "en",
        client: Optional[httpx.AsyncClient] = None,
    ) -> AssistantMessageResponse:
        """Sends caller utterance to POST /api/v1/assistant/message and returns validated response."""
        request_payload = AssistantMessageRequest(
            message=message,
            channel="IVR",
            conversation_id=conversation_id,
            case_id=case_id,
            caller_phone=caller_phone,
            language=language,
        ).model_dump(exclude_none=True)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Sanjeevani-IVR-Adapter/0.1.0",
        }

        async def _execute_post(http_client: httpx.AsyncClient) -> httpx.Response:
            return await http_client.post(
                self.endpoint_url,
                json=request_payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )

        attempts = 0
        last_error = None

        while attempts <= self.max_retries:
            attempts += 1
            try:
                if client is not None:
                    response = await _execute_post(client)
                else:
                    async with httpx.AsyncClient() as default_client:
                        response = await _execute_post(default_client)

                if response.status_code == 200:
                    data = response.json()
                    return AssistantMessageResponse(
                        response_text=data.get("response_text", EMERGENCY_FALLBACK_TEXT),
                        next_action=data.get("next_action", "CONTINUE"),
                        conversation_id=data.get("conversation_id") or conversation_id or "session-unknown",
                        case_id=data.get("case_id") or case_id,
                        case_status=data.get("case_status"),
                        facilities=data.get("facilities"),
                        safety_disclaimer=data.get("safety_disclaimer"),
                        is_fallback=False,
                    )
                else:
                    logger.warning(
                        "Backend returned HTTP %s: %s",
                        response.status_code,
                        response.text,
                    )
                    # Non-200 responses should not blindly retry to avoid duplicate case creation
                    break

            except httpx.ConnectError as ce:
                logger.warning("Connection to backend failed (attempt %d): %s", attempts, ce)
                last_error = ce
            except httpx.TimeoutException as te:
                logger.warning("Backend request timed out (attempt %d): %s", attempts, te)
                last_error = te
                # Do not retry on timeouts: the backend might have already processed the case
                break
            except Exception as e:
                logger.error("Unexpected error contacting backend: %s", e, exc_info=True)
                last_error = e
                break

        logger.error(
            "Backend communication failed (%s). Triggering emergency safety fallback.",
            last_error,
        )
        return self._create_fallback_response(conversation_id, case_id)
