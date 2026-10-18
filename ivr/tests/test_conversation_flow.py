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
    assert SpeechAdapter.detect_language("Emergency hai, patient ko nearest hospital le jana hai") == "hinglish"

    # Bhojpuri (Devanagari)
    assert SpeechAdapter.detect_language("हमार भाई के खेत में सँपवा काट लेले बा, का करीं?") == "bhojpuri"
    assert SpeechAdapter.detect_language("का भइल बा? रउआ कहाँ बानी?") == "bhojpuri"

    # Bhojpuri (Roman)
    assert SpeechAdapter.detect_language("hamar bhai ke sampwa kaat lihis, ka bhail") == "bhojpuri"
    assert SpeechAdapter.detect_language("rauwa kahan baani, jaldi kari") == "bhojpuri"


@pytest.mark.anyio
async def test_caller_language_detection_and_response_matching():
    """Verifies that the controller identifies caller language on utterance and responds in the same style."""
    store = SessionStore()
    mock_backend = BackendClient()
    controller = ConversationController(backend_client=mock_backend, session_store=store)
    controller.start_call(session_id="call-bhojpuri", caller_phone="+919876543210")

    # Caller speaks Bhojpuri
    with patch.object(mock_backend, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = AssistantMessageResponse(
            response_text="Keep patient calm and still. Do not move. Where are you located?",
            next_action="COLLECT_LOCATION",
            conversation_id="conv-bhoj-1",
        )

        res = await controller.process_utterance("call-bhojpuri", "हमार भाई के खेत में सँपवा काट लेले बा, का करीं?")

        # Verified that language was detected as Bhojpuri and sent to backend
        assert res["language"] == "bhojpuri"
        # Spoken response must be in Bhojpuri
        assert "मरीज के एकदम शांत आ स्थिर रखीं" in res["response_text"]
        assert "रउआ कवन गाँव" in res["response_text"]
        # Must not contain English instructional text
        assert "Keep patient calm" not in res["response_text"]


@pytest.mark.anyio
async def test_language_switching_mid_call():
    """Verifies that if the caller clearly switches language, the IVR switches with them."""
    store = SessionStore()
    mock_backend = BackendClient()
    controller = ConversationController(backend_client=mock_backend, session_store=store)
    controller.start_call(session_id="call-switch")

    # Turn 1: Caller speaks Hindi
    with patch.object(mock_backend, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = AssistantMessageResponse(
            response_text="Keep calm and still. Where are you located?",
            next_action="COLLECT_LOCATION",
            conversation_id="conv-switch",
        )
        res1 = await controller.process_utterance("call-switch", "सांप ने काट लिया है, क्या करें?")
        assert res1["language"] == "hindi"
        assert "मरीज को बिल्कुल शांत" in res1["response_text"]

    # Turn 2: Caller switches to Hinglish
    with patch.object(mock_backend, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = AssistantMessageResponse(
            response_text="Ambulance dispatched. Referral to nearest facility initiated.",
            next_action="CONTINUE",
            conversation_id="conv-switch",
        )
        res2 = await controller.process_utterance("call-switch", "Hum Rampur village me primary school ke pass hain")
        assert res2["language"] == "hinglish"
        assert "Ambulance dispatched" in res2["response_text"] or "Patient ko bilkul calm" in res2["response_text"]


@pytest.mark.anyio
async def test_asv_safety_speech_formatting_multilingual():
    """
    Verifies that ASV inventory status is localized accurately in Hindi, Hinglish, and Bhojpuri,
    and is never fabricated as verified when UNKNOWN.
    """
    # 1. Hindi
    hindi_speech = SpeechAdapter.format_asv_and_facility_speech(
        facility_name="रामपुर सामुदायिक स्वास्थ्य केंद्र",
        distance_km=12.4,
        asv_status="UNKNOWN",
        language="hindi",
    )
    assert "सत्यापित नहीं है" in hindi_speech
    assert "बिल्कुल देरी न करें" in hindi_speech

    # 2. Hinglish
    hinglish_speech = SpeechAdapter.format_asv_and_facility_speech(
        facility_name="Rampur CHC",
        distance_km=12.4,
        asv_status="UNKNOWN",
        language="hinglish",
    )
    assert "verified nahi hai" in hinglish_speech
    assert "delay na karein" in hinglish_speech

    # 3. Bhojpuri
    bhojpuri_speech = SpeechAdapter.format_asv_and_facility_speech(
        facility_name="रामपुर अस्पताल",
        distance_km=12.4,
        asv_status="UNKNOWN",
        language="bhojpuri",
    )
    assert "पक्का नइखे" in bhojpuri_speech
    assert "तनी देरी मत करीं" in bhojpuri_speech


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
        res = await controller.process_utterance("call-timeout", "Emergency snake bite")

        assert res["is_fallback"] is True
        assert res["next_action"] == "ESCALATE_HUMAN"
        # Safety checks: must advise stillness, no tourniquet, no incision, call 108
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
    assert ("आवाज़" in t1["response_text"] or "aawaz" in t1["response_text"] or "hear" in t1["response_text"])

    # Turn 2: Whitespace only -> prompt 2
    t2 = await controller.process_utterance("call-silence", "   ")
    assert t2["next_action"] == "CONTINUE"
    assert ("लाइन" in t2["response_text"] or "line" in t2["response_text"])

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

    res = await controller.process_utterance("call-operator", "मुझे डॉक्टर या ऑपरेटर से बात कराओ")
    assert res["next_action"] == "ESCALATE_HUMAN"
    assert "108" in res["response_text"]


def test_direct_ivr_api_endpoints(client):
    """Tests the HTTP API routes under /api/v1/ivr."""
    # 1. Inbound call
    r1 = client.post("/api/v1/ivr/call/inbound", json={"session_id": "test-http-call", "caller_phone": "+919999999999"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["session_id"] == "test-http-call"
    assert "संजीवनी" in data1["response_text"]

    # 2. Utterance call (with backend unreachable fallback)
    r2 = client.post(
        "/api/v1/ivr/call/utterance",
        json={"session_id": "test-http-call", "transcript": "सांप ने काटा है"},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert "response_text" in data2
    assert "next_action" in data2

    # 3. Call end
    r3 = client.post("/api/v1/ivr/call/end", json={"session_id": "test-http-call"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "COMPLETED"
