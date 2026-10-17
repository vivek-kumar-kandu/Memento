import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient

# Ensure ivr directory is in sys.path
_IVR_DIR = Path(__file__).resolve().parent.parent
if str(_IVR_DIR) not in sys.path:
    sys.path.insert(0, str(_IVR_DIR))

from main import app  # noqa: E402
from conversation import ConversationController, SessionStore  # noqa: E402
from backend_client import BackendClient, EMERGENCY_FALLBACK_TEXT  # noqa: E402
from speech import SpeechAdapter  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def clean_controller():
    client = BackendClient(endpoint_url="http://127.0.0.1:8000/api/v1/assistant/message")
    store = SessionStore()
    return ConversationController(backend_client=client, session_store=store)


def test_inbound_greeting_en(clean_controller):
    """Verifies that an inbound call starts with the expected English greeting."""
    res = clean_controller.start_call(session_id="call-001", caller_phone="+919876543210", language="en")
    assert res["session_id"] == "call-001"
    assert res["next_action"] == "CONTINUE"
    assert "Sanjeevani Emergency Assistance" in res["response_text"]
    assert "describe the emergency" in res["response_text"]


def test_inbound_greeting_hi(clean_controller):
    """Verifies that an inbound call supports Hindi greeting when requested."""
    res = clean_controller.start_call(session_id="call-002", caller_phone="+919876543210", language="hi")
    assert "Sanjeevani emergency helpline" in res["response_text"]
    assert "kripya" in res["response_text"].lower()


@pytest.mark.anyio
async def test_full_two_turn_snakebite_and_location_flow():
    """
    Simulates complete two-turn conversation:
    Turn 1: Caller reports snakebite -> Backend creates case and returns COLLECT_LOCATION.
    Turn 2: Caller provides location -> Backend associates facilities and returns CONTINUE.
    Verifies that conversation_id and case_id are preserved across turns.
    """
    store = SessionStore()
    mock_backend = BackendClient()

    # Mock responses for the two turns
    turn1_backend_response = {
        "response_text": "Keep the patient calm and still. Do not walk. Where are you located?",
        "next_action": "COLLECT_LOCATION",
        "conversation_id": "conv-uuid-12345",
        "case_id": "case-9988",
        "case_status": "CREATED",
        "facilities": None,
    }

    turn2_backend_response = {
        "response_text": "Ambulance dispatched. Referral to nearest facility initiated.",
        "next_action": "CONTINUE",
        "conversation_id": "conv-uuid-12345",
        "case_id": "case-9988",
        "case_status": "TRIAGED",
        "facilities": [
            {
                "facility_id": "FAC-001",
                "facility_name": "Rampur Community Health Centre",
                "distance_km": 12.4,
                "asv_stock_status": "UNKNOWN",
            }
        ],
    }

    controller = ConversationController(backend_client=mock_backend, session_store=store)
    controller.start_call(session_id="call-100", caller_phone="+919876543210")

    # Turn 1: Snakebite reported
    with patch.object(mock_backend, "send_message", new_callable=AsyncMock) as mock_send:
        from backend_client import AssistantMessageResponse

        mock_send.return_value = AssistantMessageResponse(**turn1_backend_response)

        res1 = await controller.process_utterance("call-100", "A snake bit my brother on his foot in the field!")

        # Verify outgoing request parameters passed to backend client
        mock_send.assert_called_once_with(
            message="A snake bit my brother on his foot in the field!",
            conversation_id=None,
            case_id=None,
            caller_phone="+919876543210",
            language="en",
        )

        assert res1["conversation_id"] == "conv-uuid-12345"
        assert res1["case_id"] == "case-9988"
        assert res1["next_action"] == "COLLECT_LOCATION"

    # Turn 2: Location provided (Village Rampur near primary school)
    with patch.object(mock_backend, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = AssistantMessageResponse(**turn2_backend_response)

        res2 = await controller.process_utterance("call-100", "We are in Village Rampur, near the primary school")

        # Verify that conversation_id and case_id from Turn 1 are preserved and sent
        mock_send.assert_called_once_with(
            message="We are in Village Rampur, near the primary school",
            conversation_id="conv-uuid-12345",
            case_id="case-9988",
            caller_phone="+919876543210",
            language="en",
        )
        assert res2["conversation_id"] == "conv-uuid-12345"
        assert res2["case_id"] == "case-9988"
        # Facility info should be appended to speech
        assert "Rampur Community Health Centre" in res2["response_text"]
        # Safety rule: unverified ASV should be explicitly warned
        assert "unverified" in res2["response_text"].lower()


@pytest.mark.anyio
async def test_asv_safety_speech_formatting():
    """Verifies that ASV inventory status is never fabricated as verified when UNKNOWN."""
    unknown_speech = SpeechAdapter.format_asv_and_facility_speech(
        facility_name="Civil Hospital",
        distance_km=8.5,
        asv_status="UNKNOWN",
    )
    assert "unverified" in unknown_speech.lower()
    assert "do not delay transport" in unknown_speech.lower()

    available_speech = SpeechAdapter.format_asv_and_facility_speech(
        facility_name="District Hospital",
        distance_km=25.0,
        asv_status="AVAILABLE",
    )
    assert "reported available" in available_speech.lower()
    assert "dispatch should still confirm" in available_speech.lower()


@pytest.mark.anyio
async def test_backend_timeout_and_network_failure_fallback():
    """
    Verifies that backend timeouts and network failures trigger safe
    clinician-approved fallback instructions and escalate to human.
    """
    mock_backend = BackendClient(max_retries=0)
    store = SessionStore()
    controller = ConversationController(backend_client=mock_backend, session_store=store)
    controller.start_call(session_id="call-timeout", caller_phone="+919876543210")

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timed out")):
        res = await controller.process_utterance("call-timeout", "Emergency! Snake bite!")

        assert res["is_fallback"] is True
        assert res["next_action"] == "ESCALATE_HUMAN"
        # Safety checks: must advise stillness, no tourniquet, no incision, call 108
        assert "calm and completely still" in res["response_text"].lower()
        assert "tourniquet" in res["response_text"].lower()
        assert "108" in res["response_text"]


@pytest.mark.anyio
async def test_silence_and_no_input_handling_prevents_infinite_loops():
    """
    Verifies that empty speech or silence triggers re-prompts,
    and after exceeding MAX_NO_INPUT_RETRIES (2), safely escalates to human without looping.
    """
    store = SessionStore()
    controller = ConversationController(session_store=store)
    controller.start_call(session_id="call-silence")

    # Turn 1: Empty input -> prompt 1
    t1 = await controller.process_utterance("call-silence", "")
    assert t1["next_action"] == "CONTINUE"
    assert "could not hear" in t1["response_text"].lower()

    # Turn 2: Whitespace only -> prompt 2
    t2 = await controller.process_utterance("call-silence", "   ")
    assert t2["next_action"] == "CONTINUE"
    assert "remain on the line" in t2["response_text"].lower()

    # Turn 3: Exceeds max retries -> Escalate to human
    t3 = await controller.process_utterance("call-silence", None)
    assert t3["next_action"] == "ESCALATE_HUMAN"
    assert t3["is_fallback"] is True


@pytest.mark.anyio
async def test_human_operator_escalation_intent():
    """Verifies that requesting human/operator immediately triggers escalation."""
    store = SessionStore()
    controller = ConversationController(session_store=store)
    controller.start_call(session_id="call-operator")

    res = await controller.process_utterance("call-operator", "I need to talk to a human operator or doctor please")
    assert res["next_action"] == "ESCALATE_HUMAN"
    assert "emergency coordinator" in res["response_text"].lower()


def test_direct_ivr_api_endpoints(client):
    """Tests the HTTP API routes under /api/v1/ivr."""
    # 1. Inbound call
    r1 = client.post("/api/v1/ivr/call/inbound", json={"session_id": "test-http-call", "caller_phone": "+919999999999"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["session_id"] == "test-http-call"
    assert "Sanjeevani" in data1["response_text"]

    # 2. Utterance call (with backend unreachable fallback)
    r2 = client.post(
        "/api/v1/ivr/call/utterance",
        json={"session_id": "test-http-call", "transcript": "Snake bite in jungle"},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert "response_text" in data2
    assert "next_action" in data2

    # 3. Call end
    r3 = client.post("/api/v1/ivr/call/end", json={"session_id": "test-http-call"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "COMPLETED"
