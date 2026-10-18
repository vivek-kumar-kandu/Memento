"""
test_edesy.py — Legacy Edesy endpoint integration tests.
Updated to match the new 3-symptom → location → PHC/CHC flow.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_edesy_tool_endpoint_turn1():
    """
    Turn 1 of the symptom flow: caller reports snake bite.
    The endpoint records the answer to Q1 and returns Q2.
    conversation_id is set only after assistant_service is called (during location turn).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-test-call-101-v2",
                "transcript": "Help, snake bit my hand in Lucknow!",
                "caller_phone": "+919876543210",
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert "response_text" in data
    # Turn 1 returns Q2 (next symptom question) with next_action CONTINUE
    assert data["next_action"] == "CONTINUE"
    assert data["end_call"] is False
    # conversation_id and case_id are set only after the facility lookup turn
    # (the old test assumed they were set immediately — that was the broken behaviour)


@pytest.mark.asyncio
async def test_edesy_webhook_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/webhook",
            json={
                "call_sid": "edesy-test-call-101-v2",
                "event_type": "call.ended",
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "received"
    assert data["call_sid"] == "edesy-test-call-101-v2"


@pytest.mark.asyncio
async def test_edesy_two_turn_bakshi_ka_talab_lucknow():
    """
    3-turn flow ending in a real Lucknow PHC/CHC lookup.
    - Turn 1: snakebite report → Q2 returned (next_action=CONTINUE)
    - Turn 2: Q2 answer     → Q3 returned (next_action=CONTINUE)
    - Turn 3: Q3 answer + location → facility lookup (next_action=DISPATCH_OR_TRANSPORT / CALL_108)

    Verifies that:
    - 'Tala (0.0 km)' from Maharashtra does NOT appear.
    - A genuine Lucknow facility is returned OR an honest no-result message.
    - No Case ID appears in any response_text.
    """
    import re
    _ID_RE = re.compile(r"DS-\d{4}-[A-Z0-9]+|Case ID", re.IGNORECASE)

    call_sid = "edesy-test-bkt-lucknow-v2"
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
        # New flow: Turn 1 returns Q2, next_action is CONTINUE
        assert data1["next_action"] == "CONTINUE"
        assert not _ID_RE.search(data1["response_text"]), (
            f"Case ID in turn 1 response: {data1['response_text']}"
        )

        # Turn 2: Answer Q2
        res2 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": call_sid,
                "transcript": "Nahi, theek hai",
                "caller_phone": "+919111122223",
            },
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["next_action"] == "CONTINUE"

        # Turn 3: Answer Q3 with embedded location → triggers facility lookup
        res3 = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": call_sid,
                "transcript": "Hum Lucknow mein Bakshi Ka Talab ke paas hain nahi sujan",
                "caller_phone": "+919111122223",
            },
        )
        assert res3.status_code == 200
        data3 = res3.json()

    resp_text = data3["response_text"]

    # Must NOT return Tala in Maharashtra
    assert "Tala (" not in resp_text
    assert "0.0 km" not in resp_text

    # No Case ID in spoken text
    assert not _ID_RE.search(resp_text), f"Case ID in turn 3 response: {resp_text}"

    # Must return a genuine Lucknow facility OR honest no-result
    real_facs = ["ITAUNJA", "BKT", "MAHONA", "KATHWARA", "CHC", "PHC"]
    no_result = ["nahi mila", "30 km mein koi", "108 emergency"]
    has_real = any(f in resp_text.upper() for f in real_facs)
    has_honest = any(p in resp_text.lower() for p in no_result)
    assert has_real or has_honest, (
        f"Neither real facility nor honest no-result in Turn 3: {resp_text}"
    )

    # conversation_id must be set after assistant_service is called
    assert data3.get("conversation_id") is not None, (
        "Expected conversation_id set after facility lookup"
    )
    # next_action must not be CONTINUE (must reflect facility search result)
    assert data3["next_action"] in (
        "DISPATCH_OR_TRANSPORT", "CALL_108", "CONFIRM_EMERGENCY", "COLLECT_LOCATION"
    ), f"Unexpected next_action: {data3['next_action']}"


@pytest.mark.asyncio
async def test_edesy_ambiguous_location_requests_clarification():
    """
    Ambiguous location ('khet mein hain') during the location step must
    request clarification (or honest no-result) — must NOT fabricate a facility.
    """
    call_sid = "edesy-test-ambiguous-v2"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Turn 1
        await client.post(
            "/api/v1/edesy/tool",
            json={"call_sid": call_sid, "transcript": "Saanp ne kaata hai"},
        )
        # Turn 2
        await client.post(
            "/api/v1/edesy/tool",
            json={"call_sid": call_sid, "transcript": "Nahi"},
        )
        # Turn 3 — Q3 answer (ambiguous location embedded)
        res3 = await client.post(
            "/api/v1/edesy/tool",
            json={"call_sid": call_sid, "transcript": "Nahi"},
        )
        assert res3.status_code == 200
        # Turn 4 — extremely vague location
        res4 = await client.post(
            "/api/v1/edesy/tool",
            json={"call_sid": call_sid, "transcript": "khet"},
        )

    assert res4.status_code == 200
    data4 = res4.json()
    # Must NOT fabricate a facility
    assert "Nearest healthcare facility" not in data4["response_text"]
    # Must NOT claim 0.0 km
    assert "0.0 km" not in data4["response_text"]
    # next_action is COLLECT_LOCATION (clarification) or CALL_108 (honest no-result)
    assert data4["next_action"] in ("COLLECT_LOCATION", "CALL_108", "DISPATCH_OR_TRANSPORT", "ESCALATE_HUMAN")
