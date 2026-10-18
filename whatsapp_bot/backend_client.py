import logging
from typing import Any, Dict, Optional
import httpx

try:
    from config import ASSISTANT_ENDPOINT, BACKEND_TIMEOUT_SECONDS, MAX_BACKEND_RETRIES
    from models import (
        AssistantMessageRequest,
        AssistantMessageResponse,
        GPSLocationPayload,
        EMERGENCY_FALLBACK_TEXT,
    )
except ImportError:
    from .config import ASSISTANT_ENDPOINT, BACKEND_TIMEOUT_SECONDS, MAX_BACKEND_RETRIES
    from .models import (
        AssistantMessageRequest,
        AssistantMessageResponse,
        GPSLocationPayload,
        EMERGENCY_FALLBACK_TEXT,
    )

logger = logging.getLogger("whatsapp.backend_client")


class BackendClient:
    """Asynchronous HTTP Client connecting the WhatsApp Adapter to Dhwani-Sanjeevani FastAPI Backend."""

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
        self,
        conversation_id: Optional[str] = None,
        case_id: Optional[str] = None,
        error_context: str = "",
    ) -> AssistantMessageResponse:
        """Returns safe clinician-approved emergency fallback guidance when the backend is unavailable."""
        cid = conversation_id or "fallback-session-wa"
        logger.warning(
            "Generating emergency fallback response for session %s (case %s). Reason: %s",
            cid,
            case_id,
            error_context,
        )
        return AssistantMessageResponse(
            conversation_id=cid,
            intent="emergency_fallback",
            intent_confidence=1.0,
            response_text=EMERGENCY_FALLBACK_TEXT,
            case_id=case_id,
            case_status="ESCALATED",
            next_action="ESCALATE_HUMAN",
            missing_information=[],
            nearby_facilities=None,
            referral=None,
            safety_metadata={
                "asv_verification_status": "UNKNOWN/NOT_VERIFIED",
                "asv_safety_notice": "Anti-Snake Venom (ASV) availability is NOT GUARANTEED without live confirmation. Call 108 emergency ambulance immediately.",
                "tourniquet_warning": "Do NOT remove any tourniquet in the field if already applied.",
                "backend_status": "UNREACHABLE",
            },
            is_fallback=True,
        )

    async def send_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        case_id: Optional[str] = None,
        location: Optional[GPSLocationPayload] = None,
        context: Optional[Dict[str, Any]] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> AssistantMessageResponse:
        """Sends user message and context to POST /api/v1/assistant/message and returns validated response.

        Never retries blindly on non-idempotent emergency requests.
        """
        request_obj = AssistantMessageRequest(
            channel="WHATSAPP",
            conversation_id=conversation_id,
            message=message,
            case_id=case_id,
            location=location,
            context=context or {},
        )
        payload = request_obj.model_dump(exclude_none=True)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Sanjeevini-WhatsApp-Bot/1.0.0",
        }

        async def _execute_post(http_client: httpx.AsyncClient) -> httpx.Response:
            return await http_client.post(
                self.endpoint_url,
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )

        attempts = 0
        last_error: Optional[Exception] = None

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
                    return AssistantMessageResponse(**data)
                elif response.status_code == 422:
                    logger.error("Backend validation error (422): %s", response.text)
                    return self._create_fallback_response(
                        conversation_id=conversation_id,
                        case_id=case_id,
                        error_context=f"Backend 422: {response.text}",
                    )
                else:
                    logger.error(
                        "Backend returned unexpected HTTP %s: %s",
                        response.status_code,
                        response.text,
                    )
                    # Non-200 responses should not blindly retry to avoid duplicate case creation
                    break

            except httpx.ConnectError as ce:
                logger.warning("Connection to backend failed (attempt %d/%d): %s", attempts, self.max_retries + 1, ce)
                last_error = ce
            except httpx.TimeoutException as te:
                logger.warning("Backend request timed out (attempt %d/%d): %s", attempts, self.max_retries + 1, te)
                last_error = te
            except Exception as ex:
                logger.error("Unexpected error communicating with backend: %s", ex, exc_info=True)
                last_error = ex
                break

        return self._create_fallback_response(
            conversation_id=conversation_id,
            case_id=case_id,
            error_context=str(last_error) if last_error else "Backend connection failed",
        )


# Global singleton backend client
backend_client = BackendClient()
