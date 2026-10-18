import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_edesy_tool_endpoint_turn1():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-test-call-101",
                "transcript": "Help, snake bit my hand in Lucknow!",
                "caller_phone": "+919876543210",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "response_text" in data
        assert data["next_action"] in ["COLLECT_LOCATION", "DISPATCH_OR_TRANSPORT", "CONTINUE"]
        assert data["conversation_id"] is not None
        assert data["case_id"] is not None
        assert data["end_call"] is False


@pytest.mark.asyncio
async def test_edesy_webhook_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/webhook",
            json={
                "call_sid": "edesy-test-call-101",
                "event_type": "call.ended",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "received"
        assert data["call_sid"] == "edesy-test-call-101"


@pytest.mark.asyncio
async def test_edesy_two_turn_bakshi_ka_talab_lucknow():
    """Verify that 'Hum Lucknow mein Bakshi Ka Talab ke paas hain.' resolves to genuine
    facilities in Lucknow (ITAUNJA / BKT) with real distance, preserving conversation_id and case_id.
    Explicitly verifies that 'Tala (0.0 km)' from Maharashtra does NOT appear.
    """
    call_sid = "edesy-test-bkt-lucknow-1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Turn 1: Caller reports snakebite
        res1 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": call_sid,
                "transcript": "Saanp ne kaat liya hai madad karo",
                "caller_phone": "+919111122223",
            },
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["next_action"] == "COLLECT_LOCATION"
        conv_id = data1["conversation_id"]
        case_id = data1["case_id"]
        assert conv_id is not None
        assert case_id is not None

        # Turn 2: Caller provides location: "Hum Lucknow mein Bakshi Ka Talab ke paas hain."
        res2 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": call_sid,
                "transcript": "Hum Lucknow mein Bakshi Ka Talab ke paas hain.",
                "caller_phone": "+919111122223",
            },
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["next_action"] == "DISPATCH_OR_TRANSPORT"
        # Session continuity
        assert data2["conversation_id"] == conv_id
        assert data2["case_id"] == case_id

        resp_text = data2["response_text"]
        # Must NOT return Tala in Maharashtra
        assert "Tala (" not in resp_text
        assert "0.0 km" not in resp_text

        # Must return genuine Lucknow facility (ITAUNJA or BKT)
        assert any(fac in resp_text for fac in ["ITAUNJA", "BKT", "PHC MAHONA", "KATHWARA"])
        # Distance must be real (e.g. 4.2 km)
        assert "km" in resp_text
        # Referral must be marked PENDING
        assert "PENDING" in resp_text


@pytest.mark.asyncio
async def test_edesy_ambiguous_location_requests_clarification():
    """Verify that ambiguous or non-geographic utterances ask for clarification
    rather than fabricating an arbitrary facility or returning 0.0 km.
    """
    call_sid = "edesy-test-ambiguous-1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Turn 1: Emergency report
        res1 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": call_sid,
                "transcript": "Saanp ne kaata hai",
            },
        )
        assert res1.status_code == 200
        conv_id = res1.json()["conversation_id"]
        case_id = res1.json()["case_id"]

        # Turn 2: Ambiguous location
        res2 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": call_sid,
                "transcript": "Hum khet mein hain madad karo",
            },
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["conversation_id"] == conv_id
        assert data2["case_id"] == case_id
        # Requests clarification
        assert data2["next_action"] == "COLLECT_LOCATION"
        # Does NOT fabricate a facility or distance
        assert "Nearest healthcare facility" not in data2["response_text"]
        assert "0.0 km" not in data2["response_text"]


def test_geo_index_resolution_accuracy():
    """Directly test GeoSpatialIndex resolution for ground truth dataset matching."""
    from app.services.geo_service import geo_index

    assert geo_index.is_loaded

    # 1. Bakshi Ka Talab in Lucknow
    label, coords = geo_index.resolve_location_text("Hum Lucknow mein Bakshi Ka Talab ke paas hain.")
    assert label is not None
    assert "Bakshi Ka Talab" in label
    assert "Lucknow" in label
    assert coords is not None
    lat, lon = coords
    assert 26.9 <= lat <= 27.2
    assert 80.8 <= lon <= 81.1

    # 2. Mohanlalganj in Lucknow
    label, coords = geo_index.resolve_location_text("We are in Mohanlalganj, Lucknow")
    assert label is not None
    assert "Mohanlalganj" in label
    assert "Lucknow" in label

    # 3. Naive substring 'tala' in 'talab' must NOT match Tala in Maharashtra
    label, coords = geo_index.resolve_location_text("hum talab ke paas hain")
    assert label is None
    assert coords is None

    # 4. Unknown landmark returns None
    label, coords = geo_index.resolve_location_text("Near XYZUnknownLandmark999")
    assert label is None
    assert coords is None
