import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

# Ensure ivr directory is in sys.path
_IVR_DIR = Path(__file__).resolve().parent.parent
if str(_IVR_DIR) not in sys.path:
    sys.path.insert(0, str(_IVR_DIR))

from main import app  # noqa: E402
from backend_client import AssistantMessageResponse  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_edesy_webhook_call_initiated_and_ended(client):
    """Verifies that Edesy asynchronous lifecycle events are correctly accepted and processed."""
    # 1. call.initiated event
    init_payload = {
        "event_type": "call.initiated",
        "call_sid": "edesy-sid-1001",
        "from_number": "+919876543210",
        "to_number": "+911122334455",
        "timestamp": "2026-10-18T04:00:00Z",
    }
    resp1 = client.post("/api/v1/edesy/webhook", json=init_payload)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "received"
    assert resp1.json()["call_sid"] == "edesy-sid-1001"

    # 2. call.ended event
    end_payload = {
        "event_type": "call.ended",
        "call_sid": "edesy-sid-1001",
        "duration_seconds": 45,
        "recording_url": "https://edesy.telephony.mock/recordings/edesy-sid-1001.wav",
    }
    resp2 = client.post("/api/v1/edesy/webhook", json=end_payload)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "received"


def test_edesy_webhook_signature_validation(client):
    """Verifies that webhook signature validation rejects invalid credentials when configured."""
    with patch("edesy_adapter.EDESY_WEBHOOK_SECRET", "super-secret-key"):
        payload = {
            "event_type": "call.initiated",
            "call_sid": "edesy-sid-auth-test",
        }
        # Invalid signature
        bad_resp = client.post(
            "/api/v1/edesy/webhook",
            json=payload,
            headers={"X-Edesy-Signature": "wrong-secret"},
        )
        assert bad_resp.status_code == 401

        # Valid signature
        good_resp = client.post(
            "/api/v1/edesy/webhook",
            json=payload,
            headers={"X-Edesy-Signature": "super-secret-key"},
        )
        assert good_resp.status_code == 200


def test_edesy_conversation_tool_synchronous_call(client):
    """
    Verifies that Edesy mid-call conversational AI tool call submits speech transcript
    and returns format required by Edesy voice bot.
    """
    mock_backend_resp = AssistantMessageResponse(
        response_text="Keep calm. Do not move. Where are you located?",
        next_action="COLLECT_LOCATION",
        conversation_id="edesy-conv-909",
        case_id="case-101",
        case_status="CREATED",
    )

    tool_payload = {
        "call_sid": "edesy-sid-5555",
        "transcript": "My neighbor was bitten by a cobra near his farm",
        "caller_phone": "+919876543210",
        "language": "en",
    }

    with patch("backend_client.BackendClient.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_backend_resp

        response = client.post("/api/v1/edesy/tool", json=tool_payload)
        assert response.status_code == 200
        data = response.json()

        assert "response_text" in data
        assert data["next_action"] == "COLLECT_LOCATION"
        assert data["end_call"] is False
        assert data["conversation_id"] == "edesy-conv-909"
        assert data["case_id"] == "case-101"
