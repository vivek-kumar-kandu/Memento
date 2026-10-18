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
from backend_client import BackendClient, AssistantMessageResponse  # noqa: E402
from speech import SpeechAdapter  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def clean_controller():
    client = BackendClient(endpoint_url="http://127.0.0.1:8000/api/v1/assistant/message")
    store = SessionStore()
    return ConversationController(backend_client=client, session_store=store)


def test_default_short_simple_hindi_greeting(clean_controller):
    """Verifies that an inbound call begins with a short, simple Hindi greeting by default."""
    res = clean_controller.start_call(session_id="call-001", caller_phone="+919876543210")
    assert res["session_id"] == "call-001"
    assert res["next_action"] == "CONTINUE"
    assert "संजीवनी आपातकालीन सेवा" in res["response_text"]
    assert "कहाँ हैं" in res["response_text"]


def test_language_detection():
    """Verifies language identification for Hindi, Hinglish, and Bhojpuri."""
    # Hindi (Devanagari)
    assert SpeechAdapter.detect_language("सांप ने पैर में काट लिया है, बहुत दर्द हो रहा है") == "hindi"

    # Hinglish (Roman script, mixed English-Hindi)
    assert SpeechAdapter.detect_language("Bhai mere brother ko snake bite ho gaya hai field me") == "hinglish"
    assert SpeechAdapter.detect_language("Mujhe saanp ne kaat liya hai, jaldi madad chahiye") == "hinglish"

    # Bhojpuri (Devanagari)
    assert SpeechAdapter.detect_language("हमार भाई के खेत में सँपवा काट लेले बा, का करीं?") == "bhojpuri"
    assert SpeechAdapter.detect_language("का भइल बा? रउआ कहाँ बानी?") == "bhojpuri"

    # Bhojpuri (Roman)
    assert SpeechAdapter.detect_language("hamar bhai ke sampwa kaat lihis, ka bhail") == "bhojpuri"
    assert SpeechAdapter.detect_language("rauwa kahan baani, jaldi kari") == "bhojpuri"


@pytest.mark.anyio
async def test_emergency_utterance_with_madad_creates_real_case():
    """
    Verifies that emergency utterances containing 'madad chahiye' are NOT hijacked
    by local keywords, but are sent to the backend and return real case identifiers.
    """
    store = SessionStore()
    mock_backend = BackendClient()
    controller = ConversationController(backend_client=mock_backend, session_store=store)
    controller.start_call(session_id="call-madad", caller_phone="+919876543210")

    real_backend_response = AssistantMessageResponse(
        response_text=(
            "Emergency case recorded (Case ID: DS-2026-92E1F1). Keep the patient completely calm and strictly still. "
            "Do not cut or suck the bite wound. If a tourniquet is already tied, DO NOT remove it. "
            "Please provide your current village, landmark, or GPS coordinates."
        ),
        next_action="COLLECT_LOCATION",
        conversation_id="cf622e26-80ba-4465-92f9-abb846c8c1eb",
        case_id="DS-2026-92E1F1",
        case_status="NEW",
    )

    with patch.object(mock_backend, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = real_backend_response

        res = await controller.process_utterance("call-madad", "Mujhe saanp ne kaat liya hai, jaldi madad chahiye")

        # 1. Must call backend with message
        mock_send.assert_called_once()
        assert mock_send.call_args.kwargs["message"] == "Mujhe saanp ne kaat liya hai, jaldi madad chahiye"

        # 2. Real identifiers must be returned
        assert res["conversation_id"] == "cf622e26-80ba-4465-92f9-abb846c8c1eb"
        assert res["case_id"] == "DS-2026-92E1F1"
        assert res["case_id"] != ""
        assert res["conversation_id"] != "fallback-session"
        assert res["next_action"] == "COLLECT_LOCATION"

        # 3. Response text must preserve Case ID and first aid
        assert "DS-2026-92E1F1" in res["response_text"]
        assert "tourniquet" in res["response_text"].lower() or "पट्टी" in res["response_text"]
        assert "ambulance dispatched" not in res["response_text"].lower()


@pytest.mark.anyio
async def test_follow_up_location_turn_preserves_conversation_and_case_id():
    """
    Verifies that Turn 2 location message preserves existing conversation_id and case_id,
    and correctly handles nearby_facilities.
    """
    store = SessionStore()
    mock_backend = BackendClient()
    controller = ConversationController(backend_client=mock_backend, session_store=store)

    # Establish active call with existing IDs from Turn 1
    session = store.create(session_id="call-multiturn", caller_phone="+919876543210")
    session.conversation_id = "cf622e26-80ba-4465-92f9-abb846c8c1eb"
    session.case_id = "DS-2026-92E1F1"
    store.update(session)

    turn2_backend_response = AssistantMessageResponse(
        response_text="Location received. Nearest healthcare facility: Rampur (0.0 km away). Referral initiated with status PENDING. Please arrange immediate transport via 108 ambulance. Keep the bitten limb immobilized at heart level.",
        next_action="DISPATCH_OR_TRANSPORT",
        conversation_id="cf622e26-80ba-4465-92f9-abb846c8c1eb",
        case_id="DS-2026-92E1F1",
        case_status="REFERRAL_MADE",
        facilities=[
            {
                "facility_id": "HCF-004594",
                "facility_name": "Rampur",
                "facility_type": "PHC",
                "distance_km": 0.0,
                "asv_stock_status": "UNKNOWN",
            }
        ],
    )

    with patch.object(mock_backend, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = turn2_backend_response

        res = await controller.process_utterance("call-multiturn", "Village Rampur near Primary School")

        # Must send existing IDs
        mock_send.assert_called_once_with(
            message="Village Rampur near Primary School",
            conversation_id="cf622e26-80ba-4465-92f9-abb846c8c1eb",
            case_id="DS-2026-92E1F1",
            caller_phone="+919876543210",
            language="hinglish",
        )

        assert res["conversation_id"] == "cf622e26-80ba-4465-92f9-abb846c8c1eb"
        assert res["case_id"] == "DS-2026-92E1F1"
        assert res["next_action"] == "DISPATCH_OR_TRANSPORT"
        assert "Rampur" in res["response_text"]
        # ASV unknown stock must be communicated truthfully
        assert "verified nahi" in res["response_text"] or "सत्यापित नहीं" in res["response_text"]


@pytest.mark.anyio
async def test_backend_timeout_and_network_failure_truthful_fallback():
    """
    Verifies that backend timeouts and network failures trigger truthful fallback:
    - Never invents 'fallback-session' or fake case IDs.
    - Never claims 'Ambulance dispatched' or 'Referral initiated'.
    - Preserves clinical safety advice and directs caller to 108/112.
    """
    mock_backend = BackendClient(max_retries=0)
    store = SessionStore()
    controller = ConversationController(backend_client=mock_backend, session_store=store)
    controller.start_call(session_id="call-timeout", caller_phone="+919876543210")

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timed out")):
        res = await controller.process_utterance("call-timeout", "Emergency snake bite in field")

        assert res["is_fallback"] is True
        assert res["next_action"] == "ESCALATE_HUMAN"
        # Must NOT return 'fallback-session' or fake case ID
        assert res["conversation_id"] is None
        assert res["case_id"] is None
        # Must NOT claim ambulance dispatched
        assert "ambulance dispatched" not in res["response_text"].lower()
        assert "referral initiate" not in res["response_text"].lower()
        # Must give truthful emergency fallback advice
        assert "108" in res["response_text"] or "112" in res["response_text"]


@pytest.mark.anyio
async def test_pure_operator_request_without_emergency_escalates_truthfully():
    """
    Verifies that requesting human operator when no emergency info is provided
    returns truthful escalation prompt without false claims of active connection.
    """
    store = SessionStore()
    controller = ConversationController(session_store=store)
    controller.start_call(session_id="call-operator")

    res = await controller.process_utterance("call-operator", "operator se baat karao")
    assert res["next_action"] == "ESCALATE_HUMAN"
    # Must NOT claim connection has succeeded
    assert "connecting your call" not in res["response_text"].lower()
    assert "जोड़ा जा रहा है" not in res["response_text"]
    # Must tell truth and advise 108
    assert "108" in res["response_text"]


def test_direct_ivr_api_endpoints(client):
    """Tests the direct HTTP API routes under /api/v1/ivr."""
    # 1. Inbound call
    r1 = client.post("/api/v1/ivr/call/inbound", json={"session_id": "test-http-call", "caller_phone": "+919999999999"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["session_id"] == "test-http-call"
    assert "संजीवनी" in data1["response_text"]

    # 2. Utterance call (with backend unreachable fallback)
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        r2 = client.post(
            "/api/v1/ivr/call/utterance",
            json={"session_id": "test-http-call", "transcript": "सांप ने काटा है"},
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert "response_text" in data2
        assert data2["conversation_id"] is None
        assert data2["case_id"] is None

    # 3. Call end
    r3 = client.post("/api/v1/ivr/call/end", json={"session_id": "test-http-call"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "COMPLETED"
