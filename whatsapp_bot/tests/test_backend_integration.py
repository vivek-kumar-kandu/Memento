import pytest
import httpx
from backend_client import BackendClient
from models import GPSLocationPayload


@pytest.mark.anyio
async def test_backend_client_request_construction():
    """Verify backend client sends correct payload conforming to backend schema."""
    captured_requests = []

    async def mock_handler(request: httpx.Request):
        captured_requests.append(request)
        return httpx.Response(
            200,
            json={
                "conversation_id": "conv-test-999",
                "intent": "emergency_report",
                "intent_confidence": 0.95,
                "response_text": "Case recorded DS-2026-999. Keep patient still.",
                "case_id": "DS-2026-999",
                "case_status": "NEW",
                "next_action": "COLLECT_LOCATION",
                "missing_information": ["location"],
            },
        )

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as test_http_client:
        client = BackendClient(endpoint_url="http://mock-backend/api/v1/assistant/message")
        loc = GPSLocationPayload(latitude=26.8467, longitude=80.9462, village="Bakshi Ka Talab")
        resp = await client.send_message(
            message="Saanp ne kaat liya hai",
            conversation_id="conv-test-999",
            case_id="DS-2026-999",
            location=loc,
            client=test_http_client,
        )

    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req.method == "POST"

    import json
    body = json.loads(req.content.decode("utf-8"))
    assert body["channel"] == "WHATSAPP"
    assert body["message"] == "Saanp ne kaat liya hai"
    assert body["conversation_id"] == "conv-test-999"
    assert body["case_id"] == "DS-2026-999"
    assert body["location"]["latitude"] == 26.8467
    assert body["location"]["longitude"] == 80.9462
    assert body["location"]["village"] == "Bakshi Ka Talab"

    assert resp.case_id == "DS-2026-999"
    assert resp.is_fallback is False


@pytest.mark.anyio
async def test_backend_client_connection_failure_fallback():
    """Verify when backend is completely offline/unreachable, client generates safe emergency fallback."""
    # Connecting to an invalid port guaranteed to fail immediately
    client = BackendClient(endpoint_url="http://127.0.0.1:59999/api/v1/assistant/message", max_retries=0)
    resp = await client.send_message(
        message="Emergency snakebite",
        conversation_id="conv-fallback-test",
        case_id="CASE-FALLBACK-01",
    )

    assert resp.is_fallback is True
    assert resp.next_action == "ESCALATE_HUMAN"
    assert resp.case_status == "ESCALATED"
    # Verify clinical safety advice in fallback
    assert "DO NOT cut or suck" in resp.response_text or "Do not cut the wound" in resp.response_text or "calm" in resp.response_text.lower()
    assert "108" in resp.response_text
    # Tourniquet field safety rule: never tell caller to remove tourniquet
    assert "DO NOT remove" in resp.response_text or "tourniquet" in resp.safety_metadata.get("tourniquet_warning", "").lower()
    # Does NOT invent fake hospital acknowledgement
    assert resp.referral is None
