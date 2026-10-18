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
async def test_edesy_emergency_report_concise_asks_location():
    """Verify emergency report produces a concise response, confirms case creation, and asks for location."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-call-emer-01",
                "transcript": "Saanp ne kaat liya hai emergency hai madad bhejo",
                "caller_phone": "+919876543211",
            },
        )
        assert res.status_code == 200
        data = res.json()

        # Structured fields preserved
        assert data["case_id"] is not None
        assert data["case_id"].startswith("DS-")
        assert data["conversation_id"] is not None
        assert data["next_action"] == "COLLECT_LOCATION"
        assert data["end_call"] is False

        # Spoken response verification
        resp = data["response_text"]
        assert "Aap abhi kis gaon mein hain? Paas ka landmark batayein." in resp
        assert "still" in resp.lower() or "shaant" in resp.lower()
        assert "kaatein" in resp.lower() or "choosein" in resp.lower()
        assert "gaon" in resp.lower() and "landmark" in resp.lower()

        # Must not contain false dispatch statements
        assert "ambulance dispatched" not in resp.lower()
        assert "hospital contacted" not in resp.lower()
        assert "connecting you" not in resp.lower()

        # Concise length: approximately 1-3 sentences
        sentences = [s.strip() for s in resp.split(".") if s.strip()]
        assert len(sentences) <= 4


@pytest.mark.asyncio
async def test_edesy_location_verified_facility_pending_referral_unverified_asv():
    """Verify location response mentions verified facility, approximate distance, and urgent medical help reminder without routine ASV/referral recitation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Turn 1: Emergency report
        res1 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-call-loc-02",
                "transcript": "Saanp ne kaata hai jaldi madad karo",
                "caller_phone": "+919876543212",
            },
        )
        assert res1.status_code == 200
        conv_id = res1.json()["conversation_id"]
        case_id = res1.json()["case_id"]

        # Turn 2: Real coordinates (near Lucknow)
        res2 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-call-loc-02",
                "transcript": "Hum log 26.8467, 80.9462 ke paas hain",
                "caller_phone": "+919876543212",
            },
        )
        assert res2.status_code == 200
        data2 = res2.json()

        # Identifiers preserved across turns
        assert data2["conversation_id"] == conv_id
        assert data2["case_id"] == case_id
        assert data2["next_action"] == "DISPATCH_OR_TRANSPORT"

        resp = data2["response_text"]
        # Facility and distance present
        assert "Aapke paas" in resp
        assert "lagbhag" in resp and "door hai" in resp
        assert "km door" in resp
        assert "turant medical help lein" in resp.lower()

        # ASV and referral not recited routinely in speech
        assert "asv" not in resp.lower()
        assert "referral" not in resp.lower()
        assert "hospital accepted" not in resp.lower()
        assert "ambulance dispatched" not in resp.lower()


@pytest.mark.asyncio
async def test_edesy_location_unresolved_does_not_invent_facility():
    """Verify unresolvable location asks for clearer landmark/district and does not fabricate coordinates/facilities."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Turn 1: Register case
        res1 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-call-unresolved-03",
                "transcript": "Help snake bite emergency",
                "caller_phone": "+919876543213",
            },
        )
        conv_id = res1.json()["conversation_id"]
        case_id = res1.json()["case_id"]

        # Turn 2: Unknown fictional village
        res2 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-call-unresolved-03",
                "transcript": "Hum log XYZFictionalUnknownVillage123 me hain",
                "caller_phone": "+919876543213",
            },
        )
        assert res2.status_code == 200
        data2 = res2.json()

        assert data2["conversation_id"] == conv_id
        assert data2["case_id"] == case_id
        assert data2["next_action"] == "COLLECT_LOCATION"

        resp = data2["response_text"]
        # Asks for district, block, or prominent landmark
        assert "district" in resp.lower() or "block" in resp.lower() or "landmark" in resp.lower()
        # Does NOT invent a facility or distance
        assert "km door" not in resp.lower()
        assert "ambulance dispatched" not in resp.lower()


@pytest.mark.asyncio
async def test_edesy_first_aid_query_preserves_tourniquet_warning():
    """Verify first-aid guidance preserves critical tourniquet safety warning."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-call-fa-04",
                "transcript": "What first aid should we do? Should we cut the wound or untie the tight cloth?",
                "caller_phone": "+919876543214",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["next_action"] == "PROVIDE_FIRST_AID"

        resp = data["response_text"]
        # Clinician-reviewed tourniquet safety warning
        assert "tourniquet" in resp.lower()
        assert "na hatayein" in resp.lower() or "do not remove" in resp.lower()
        assert "cut" in resp.lower()
        assert "108" in resp


@pytest.mark.asyncio
async def test_edesy_human_escalation_truthful_no_false_transfer():
    """Verify human help request does not claim an automated transfer or ambulance dispatch occurred."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-call-esc-05",
                "transcript": "Mujhe human operator se baat karni hai please connect karo",
                "caller_phone": "+919876543215",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["next_action"] == "ESCALATE_HUMAN"

        resp = data["response_text"]
        # Truthful statement about transfer
        assert "available nahi hai" in resp.lower()
        assert "108" in resp
        assert "connecting you" not in resp.lower()
        assert "ambulance dispatched" not in resp.lower()


@pytest.mark.asyncio
async def test_edesy_bhojpuri_language_support():
    """Verify Bhojpuri language detection and natural dialect response."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-call-bhoj-06",
                "transcript": "हमार बाबू के खेत में साँप काट लेले बा, बहुत दर्द बा",
                "caller_phone": "+919876543216",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["language"] == "bhojpuri"
        assert "रखीं" in data["response_text"] or "बानी" in data["response_text"]
        assert data["case_id"] is not None


@pytest.mark.asyncio
async def test_edesy_silence_retry_and_escalation():
    """Verify handling of caller silence: retry prompt on attempts 1-2, escalation on attempt 3."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        call_sid = "edesy-call-silence-07"

        # Attempt 1: Silence
        r1 = await client.post("/api/v1/edesy/tool", json={"call_sid": call_sid, "transcript": ""})
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["next_action"] == "CONTINUE"
        assert len(d1["response_text"]) > 0

        # Attempt 2: Silence
        r2 = await client.post("/api/v1/edesy/tool", json={"call_sid": call_sid, "transcript": ""})
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["next_action"] == "CONTINUE"

        # Attempt 3: Silence -> Escalation
        r3 = await client.post("/api/v1/edesy/tool", json={"call_sid": call_sid, "transcript": ""})
        assert r3.status_code == 200
        d3 = r3.json()
        assert d3["next_action"] == "ESCALATE_HUMAN"
        assert "108" in d3["response_text"]

