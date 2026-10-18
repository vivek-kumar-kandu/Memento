import logging
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

try:
    from config import ASSISTANT_ENDPOINT, BACKEND_TIMEOUT_SECONDS, MAX_BACKEND_RETRIES
except ImportError:
    from .config import ASSISTANT_ENDPOINT, BACKEND_TIMEOUT_SECONDS, MAX_BACKEND_RETRIES

logger = logging.getLogger("ivr.backend_client")

# Truthful clinician-reviewed emergency fallback (no false dispatch or transfer claims)
EMERGENCY_FALLBACK_TEXT = (
    "Emergency alert: We cannot reach the central emergency server right now. "
    "Keep the patient completely calm and strictly still. Do not walk or move the bitten limb. "
    "Do not cut the wound, suck venom, apply ice, or remove an existing tourniquet. "
    "Call 108 or 112 emergency ambulance immediately for transport."
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
    conversation_id: Optional[str] = Field(default=None, description="Unique conversation session ID")
    case_id: Optional[str] = Field(default=None, description="Emergency case ID")
    case_status: Optional[str] = Field(default=None, description="Current case status")
    facilities: Optional[List[Dict[str, Any]]] = Field(default=None, description="Nearby facilities")
    referral: Optional[Dict[str, Any]] = Field(default=None, description="Referral information")
    safety_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Safety metadata from backend")
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
        """
        Returns safe clinician-approved emergency fallback response.
        Preserves existing conversation_id and case_id if present, but NEVER invents
        fake IDs such as 'fallback-session'.
        """
        return AssistantMessageResponse(
            response_text=EMERGENCY_FALLBACK_TEXT,
            next_action="ESCALATE_HUMAN",
            conversation_id=conversation_id,
            case_id=case_id,
            case_status="FAILED_BACKEND_CONNECT",
            facilities=None,
            referral=None,
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
                logger.info(
                    "Outbound request to backend: POST %s (attempt %d, cid=%s, case=%s)",
                    self.endpoint_url,
                    attempts,
                    conversation_id,
                    case_id,
                )

                if client is not None:
                    response = await _execute_post(client)
                else:
                    async with httpx.AsyncClient() as default_client:
                        response = await _execute_post(default_client)

                if response.status_code == 200:
                    data = response.json()
                    resp_cid = data.get("conversation_id") or conversation_id
                    resp_case_id = data.get("case_id") or case_id
                    # Handle both nearby_facilities and facilities keys
                    fac_list = data.get("nearby_facilities") or data.get("facilities")

                    logger.info(
                        "Backend responded HTTP 200 OK: conversation_id=%s, case_id=%s, next_action=%s",
                        resp_cid,
                        resp_case_id,
                        data.get("next_action"),
                    )

                    return AssistantMessageResponse(
                        response_text=data.get("response_text", EMERGENCY_FALLBACK_TEXT),
                        next_action=data.get("next_action", "CONTINUE"),
                        conversation_id=resp_cid,
                        case_id=resp_case_id,
                        case_status=data.get("case_status"),
                        facilities=fac_list,
                        referral=data.get("referral"),
                        safety_metadata=data.get("safety_metadata"),
                        safety_disclaimer=data.get("safety_disclaimer"),
                        is_fallback=False,
                    )
                else:
                    logger.error(
                        "Backend returned HTTP %d for target %s: %s",
                        response.status_code,
                        self.endpoint_url,
                        response.text[:200],
                    )
                    # Non-200 responses should not blindly retry to avoid duplicate case creation
                    last_error = f"HTTP_{response.status_code}"
                    break

            except httpx.ConnectError as ce:
                logger.error(
                    "Backend ConnectError: target=%s, attempt=%d, exception=%s",
                    self.endpoint_url,
                    attempts,
                    type(ce).__name__,
                )
                last_error = ce
            except httpx.TimeoutException as te:
                logger.error(
                    "Backend TimeoutException: target=%s, timeout=%ss, attempt=%d",
                    self.endpoint_url,
                    self.timeout_seconds,
                    attempts,
                )
                last_error = te
                # Do not retry on timeouts: the backend might have already processed the case
                break
            except Exception as e:
                logger.error(
                    "Unexpected error contacting backend: target=%s, error=%s",
                    self.endpoint_url,
                    e,
                    exc_info=True,
                )
                last_error = e
                break

        logger.error(
            "Backend communication failed (error=%s, target=%s). Triggering emergency safety fallback.",
            last_error,
            self.endpoint_url,
        )
        return self._create_fallback_response(conversation_id, case_id)
