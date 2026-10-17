import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_assistant_emergency_multi_turn_flow(client: AsyncClient):
    """
    Test the complete 2-turn sequence:
    1. Caller reports snakebite -> creates case, asks for location.
    2. Caller supplies coordinates -> reuses conversation & case, finds facilities, creates referral.
    """
    # Turn 1: Caller reports emergency in Hinglish
    turn1_payload = {
        "channel": "IVR",
        "message": "Saanp ne kaat liya hai emergency hai madad bhejo",
    }
    res1 = await client.post("/api/v1/assistant/message", json=turn1_payload)
    assert res1.status_code == 200
    data1 = res1.json()

    conv_id = data1["conversation_id"]
    case_id = data1["case_id"]
    assert conv_id is not None
    assert case_id is not None
    assert case_id.startswith("DS-")
    assert data1["intent"] == "emergency_report"
    assert data1["next_action"] == "COLLECT_LOCATION"
    assert "location" in data1["missing_information"]
    assert "DO NOT remove" in data1["response_text"] or "do not cut" in data1["response_text"].lower()

    # Turn 2: Caller responds with coordinates around Lucknow (26.8467, 80.9462)
    turn2_payload = {
        "channel": "IVR",
        "conversation_id": conv_id,
        "message": "We are at 26.8467, 80.9462 near Lucknow",
    }
    res2 = await client.post("/api/v1/assistant/message", json=turn2_payload)
    assert res2.status_code == 200
    data2 = res2.json()

    # Case ID and Conversation ID must remain stable across turns
    assert data2["conversation_id"] == conv_id
    assert data2["case_id"] == case_id
    assert data2["case_status"] == "REFERRAL_MADE"
    assert data2["nearby_facilities"] is not None
    assert len(data2["nearby_facilities"]) > 0

    # Nearest facility allocated as referral
    assert data2["referral"] is not None
    assert data2["referral"]["referral_status"] == "PENDING"
    assert data2["referral"]["facility_id"] == data2["nearby_facilities"][0]["facility_id"]

    # Verify referral was actually recorded in Case API
    case_api_res = await client.get(f"/api/v1/cases/{case_id}/referral")
    assert case_api_res.status_code == 200
    assert case_api_res.json()["facility_id"] == data2["referral"]["facility_id"]


@pytest.mark.asyncio
async def test_assistant_location_with_village_name(client: AsyncClient):
    """Test resolving location from known subdistrict name in facility directory."""
    turn1_payload = {
        "channel": "WHATSAPP",
        "message": "Snake bit my father in the field",
    }
    res1 = await client.post("/api/v1/assistant/message", json=turn1_payload)
    conv_id = res1.json()["conversation_id"]
    case_id = res1.json()["case_id"]

    turn2_payload = {
        "channel": "WHATSAPP",
        "conversation_id": conv_id,
        "message": "Hum log Bakshi Ka Talab ke paas hain",
    }
    res2 = await client.post("/api/v1/assistant/message", json=turn2_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["conversation_id"] == conv_id
    assert data2["case_id"] == case_id
    assert data2["nearby_facilities"] is not None
    assert len(data2["nearby_facilities"]) > 0


@pytest.mark.asyncio
async def test_assistant_unresolved_village_clarification(client: AsyncClient):
    """Test that free-text unknown village asks for clarification and never fabricates coordinates."""
    # First turn creates case
    res1 = await client.post(
        "/api/v1/assistant/message",
        json={"channel": "IVR", "message": "Help, snake bite emergency!"},
    )
    conv_id = res1.json()["conversation_id"]

    # Second turn provides unknown fictional place name
    res2 = await client.post(
        "/api/v1/assistant/message",
        json={"channel": "IVR", "conversation_id": conv_id, "message": "We are at XYZFictionalPlace123"},
    )
    data2 = res2.json()
    assert data2["next_action"] == "COLLECT_LOCATION"
    assert "location" in data2["missing_information"]
    assert "Could not reliably resolve" in data2["response_text"]
    assert data2["nearby_facilities"] is None  # No fabricated facilities or coordinates


@pytest.mark.asyncio
async def test_assistant_first_aid_query(client: AsyncClient):
    """Test first aid instructions adhere strictly to clinician guidance and tourniquet warnings."""
    payload = {
        "channel": "WHATSAPP",
        "message": "What first aid should we do? Should we tie a tight cloth or cut the wound?",
    }
    res = await client.post("/api/v1/assistant/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "first_aid_query"
    assert data["next_action"] == "PROVIDE_FIRST_AID"
    assert "DO NOT cut" in data["response_text"]
    assert "DO NOT REMOVE IT in the field" in data["response_text"]


@pytest.mark.asyncio
async def test_assistant_human_escalation_override(client: AsyncClient):
    """Test human help intent triggers live escalation regardless of confidence."""
    payload = {
        "channel": "IVR",
        "message": "Mujhe doctor se baat karni hai, connect karo",
    }
    res = await client.post("/api/v1/assistant/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "human_help"
    assert data["next_action"] == "ESCALATE_HUMAN"
    assert "108 medical dispatcher" in data["response_text"]


@pytest.mark.asyncio
async def test_assistant_hindi_devanagari(client: AsyncClient):
    """Test Hindi Devanagari input handling."""
    payload = {
        "channel": "IVR",
        "message": "सांप ने काट लिया है जल्दी मदद भेजिए",
    }
    res = await client.post("/api/v1/assistant/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "emergency_report"
    assert data["case_id"] is not None


@pytest.mark.asyncio
async def test_assistant_unknown_fallback(client: AsyncClient):
    """Test safe fallback for non-emergency or unknown queries."""
    payload = {
        "channel": "IVR",
        "message": "Tell me a joke about coding",
    }
    res = await client.post("/api/v1/assistant/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "unknown"
    assert data["next_action"] == "CLARIFY"
