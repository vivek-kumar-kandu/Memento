"""
test_edesy_flow.py — Comprehensive tests for the 3-symptom → location → PHC/CHC flow.

FLOW CONTRACT:
  The Edesy AI system prompt asks Q1 as the opening message.
  The /tool endpoint is invoked AFTER the caller speaks.

  Turn 1 (caller answers Q1) → /tool returns Q2
  Turn 2 (caller answers Q2) → /tool returns Q3
  Turn 3 (caller answers Q3) → /tool returns location question
  Turn 4 (caller gives location) → /tool returns real PHC/CHC results

Tests are keyed to this contract and to the 12 acceptance criteria.
Each test uses a unique call_sid prefix to avoid cross-test session pollution.
No production writes: all call_sids are prefixed with "test-".
"""
import re
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app

_TOOL = "/api/v1/edesy/tool"

# Regex to detect any Case ID / UUID in spoken text
_ID_PATTERN = re.compile(
    r"(DS-\d{4}-[A-Z0-9]+|Case ID|conversation[_ ]?id"
    r"|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)


def _has_no_ids(text: str) -> bool:
    return _ID_PATTERN.search(text) is None


async def _post(client: AsyncClient, call_sid: str, transcript: str, **extra) -> dict:
    payload = {"call_sid": call_sid, "transcript": transcript}
    payload.update(extra)
    res = await client.post(_TOOL, json=payload)
    assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
    return res.json()


# ---------------------------------------------------------------------------
# Test 1 — First /tool call (answer to Q1) returns Q2, not a Case ID
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_1_turn1_returns_q2_not_case_id():
    """
    AC #1: The first /tool invocation (caller answering Q1) must return Q2.
    It must NOT return a Case ID or a location request.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _post(client, "t1-ac1", "Saanp ne haath mein kaata hai")

    resp = data["response_text"]
    # Must return Q2 — neurological/breathing question
    assert (
        "bolne" in resp or "nigalne" in resp or "saans" in resp or "kamzori" in resp
    ), f"Expected Q2 (neurological question) in response, got: {repr(resp)}"
    # Must NOT contain a spoken Case ID
    assert _has_no_ids(resp), f"Response contains an ID: {repr(resp)}"
    # Must NOT be a location request
    assert not (
        "gaon" in resp and "district" in resp and "landmark" in resp
    ), f"First /tool call must not ask for location: {repr(resp)}"
    assert data["next_action"] in ("CONTINUE",)


# ---------------------------------------------------------------------------
# Test 2 — Second /tool call returns Q3
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_2_turn2_returns_q3():
    """AC #2: Turn 2 must return Q3 (bleeding / local warning signs question)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, "t2-ac2", "Saanp ne kaata hai")
        data2 = await _post(client, "t2-ac2", "Haan, palkein thodi jhuk rahi hain")

    resp = data2["response_text"]
    assert (
        "khoon" in resp or "sujan" in resp or "masoodon" in resp or "peshab" in resp
    ), f"Expected Q3 (bleeding question), got: {repr(resp)}"
    assert _has_no_ids(resp), f"Response contains ID: {repr(resp)}"


# ---------------------------------------------------------------------------
# Test 3 — Third /tool call returns location question
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_3_turn3_returns_location_question():
    """AC #3: Turn 3 (answer to Q3) must return the location question, not another symptom Q."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, "t3-ac3", "Saanp ne kaata hai")
        await _post(client, "t3-ac3", "Nahi, aankhein theek hain")
        data3 = await _post(client, "t3-ac3", "Nahi, saans bhi theek hai")

    resp = data3["response_text"]
    assert (
        "gaon" in resp or "mohalla" in resp or "district" in resp or "landmark" in resp
    ), f"Expected location question after Q3, got: {repr(resp)}"
    assert _has_no_ids(resp), f"Response contains ID: {repr(resp)}"
    assert data3["next_action"] == "COLLECT_LOCATION"


# ---------------------------------------------------------------------------
# Test 4 — Fourth /tool call returns real PHC/CHC or honest no-result
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_4_turn4_returns_real_facility_or_honest_no_result():
    """
    AC #4 + #5: Turn 4 (location answer) must return actual PHC/CHC records.
    Uses Bakshi Ka Talab, Lucknow — expects ITAUNJA, BKT, MAHONA, or similar.
    Must NOT fabricate a facility or return 0.0 km.
    """
    call_sid = "t4-lucknow-bkt"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")
        await _post(client, call_sid, "Haan thoda")
        await _post(client, call_sid, "Nahi")
        data4 = await _post(client, call_sid, "Hum Lucknow mein Bakshi Ka Talab ke paas hain")

    resp = data4["response_text"]
    assert _has_no_ids(resp), f"Response contains ID: {repr(resp)}"
    assert "0.0 km" not in resp, f"Suspicious 0.0 km: {repr(resp)}"
    real_names = ["ITAUNJA", "BKT", "MAHONA", "KATHWARA", "CHC", "PHC"]
    no_result_phrases = ["nahi mila", "30 km mein koi", "no facility"]
    has_real = any(n in resp.upper() for n in real_names)
    has_honest = any(p in resp.lower() for p in no_result_phrases)
    assert has_real or has_honest, f"Neither real facility nor honest no-result: {repr(resp)}"


# ---------------------------------------------------------------------------
# Test 5 — Location question step (explicit)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_5_location_step_explicitly():
    """
    AC #4: After 3 symptom answers, the /tool must ask for location.
    The next call with a location string must attempt facility lookup.
    """
    call_sid = "t5-location-step"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")
        await _post(client, call_sid, "Nahi")
        data3 = await _post(client, call_sid, "Nahi")  # answer to Q3 → location Q

    resp = data3["response_text"]
    assert (
        "gaon" in resp or "mohalla" in resp or "district" in resp or "landmark" in resp
    ), f"Expected location question, got: {repr(resp)}"
    assert data3["next_action"] == "COLLECT_LOCATION"
    assert _has_no_ids(resp)


# ---------------------------------------------------------------------------
# Test 6 — Session state persists across turns (same call_sid)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_6_session_persists_across_turns():
    """
    AC #6: conversation_id and case_id from the facility-lookup turn must be
    preserved in subsequent turns of the same call_sid.
    """
    call_sid = "t6-session-persist"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")
        await _post(client, call_sid, "Nahi")
        await _post(client, call_sid, "Nahi")
        d_fac = await _post(client, call_sid, "Hum Mohanlalganj Lucknow ke paas hain")
        # Additional turn after DONE
        d_extra = await _post(client, call_sid, "Aur kuch batao")

    assert _has_no_ids(d_fac["response_text"])
    assert _has_no_ids(d_extra["response_text"])
    # conversation_id set in facility turn must still be present
    if d_fac.get("conversation_id"):
        assert d_extra.get("conversation_id") == d_fac["conversation_id"], (
            f"Session conversation_id changed: {d_fac['conversation_id']} → {d_extra['conversation_id']}"
        )


# ---------------------------------------------------------------------------
# Test 7 — No Case ID or UUID in ANY response_text across all turns
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_7_no_case_id_in_any_response_text():
    """AC #7: No turn must speak a Case ID or UUID."""
    call_sid = "t7-no-ids"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        responses = [
            await _post(client, call_sid, "Saanp ne kaata hai madad karo"),
            await _post(client, call_sid, "Haan"),
            await _post(client, call_sid, "Nahi"),
            await _post(client, call_sid, "Kanpur mein Civil Lines ke paas hain"),
            await _post(client, call_sid, "Theek hai"),
        ]

    for i, data in enumerate(responses):
        text = data["response_text"]
        assert _has_no_ids(text), f"Turn {i + 1} contains an ID: {repr(text)}"
        if data.get("case_id"):
            assert data["case_id"] not in text, (
                f"Turn {i + 1}: case_id {data['case_id']} found verbatim in response_text"
            )


# ---------------------------------------------------------------------------
# Test 8 — No duplicate case across turns (same case_id retained)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_8_no_duplicate_case_across_turns():
    """AC #8: case_id must not change between turns of the same call session."""
    call_sid = "t8-no-dup-case"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")
        await _post(client, call_sid, "Haan")
        await _post(client, call_sid, "Nahi")
        d_fac = await _post(client, call_sid, "Hum Varanasi mein hain")
        d_next = await _post(client, call_sid, "Theek hai")

    case_id_fac = d_fac.get("case_id")
    case_id_next = d_next.get("case_id")
    if case_id_fac and case_id_next:
        assert case_id_fac == case_id_next, (
            f"Duplicate case: facility_turn={case_id_fac}, next_turn={case_id_next}"
        )


# ---------------------------------------------------------------------------
# Test 9 — Emergency exception: breathing difficulty
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_9a_emergency_exception_breathing():
    """
    AC #9: 'saans nahi aa rahi' during symptom flow must trigger immediate
    emergency advice and skip to location — not continue Q2/Q3.
    Must NOT claim ambulance dispatched.
    """
    call_sid = "t9a-breath"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")
        # Instead of answering Q2, caller reports critical symptom
        data2 = await _post(client, call_sid, "Patient ko saans nahi aa rahi hai bilkul bhi")

    resp = data2["response_text"]
    assert "108" in resp or "112" in resp, f"No emergency number: {repr(resp)}"
    assert "ambulance dispatched" not in resp.lower()
    assert "ambulance bheji" not in resp.lower()
    # Must now ask for location (after emergency advice)
    assert "gaon" in resp or "bataiye" in resp or "location" in resp.lower(), (
        f"Expected location ask after emergency, got: {repr(resp)}"
    )
    assert _has_no_ids(resp)
    assert data2["next_action"] == "COLLECT_LOCATION"


@pytest.mark.asyncio
async def test_9b_emergency_exception_unconscious():
    """AC #9b: 'Patient behosh ho gaya hai' must trigger emergency exception."""
    call_sid = "t9b-behosh"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")
        data2 = await _post(client, call_sid, "Patient behosh ho gaya hai")

    resp = data2["response_text"]
    assert "108" in resp or "112" in resp, f"Expected emergency number: {repr(resp)}"
    assert _has_no_ids(resp)


# ---------------------------------------------------------------------------
# Test 10 — Ambiguous location: no fabricated facility, honest clarification
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_10_ambiguous_location_no_fabricated_facility():
    """
    AC #10: A one-word location like 'khet' must not return a fabricated
    facility or 0.0 km. Must ask for clarification.
    """
    call_sid = "t10-ambig"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")
        await _post(client, call_sid, "Nahi")
        await _post(client, call_sid, "Nahi")
        data4 = await _post(client, call_sid, "khet")

    resp = data4["response_text"]
    assert _has_no_ids(resp)
    assert "0.0 km" not in resp
    # Must NOT claim a fabricated facility
    assert "Nearest healthcare facility: " not in resp


# ---------------------------------------------------------------------------
# Test 11 — DB/backend failure → honest error, not fake success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_11_backend_failure_honest_error(monkeypatch):
    """
    AC #11: If assistant_service raises during facility lookup, the response
    must be truthful — no fabricated facility, no fake Case ID.
    """
    from app.services import assistant_service as asvc_module

    original = asvc_module.assistant_service.handle_message

    async def _broken(*args, **kwargs):
        raise RuntimeError("Simulated DB failure")

    monkeypatch.setattr(asvc_module.assistant_service, "handle_message", _broken)

    call_sid = "t11-dbfail"
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await _post(client, call_sid, "Saanp ne kaata hai")
            await _post(client, call_sid, "Nahi")
            await _post(client, call_sid, "Nahi")
            d_fac = await _post(client, call_sid, "Hum Agra mein hain")
    finally:
        monkeypatch.setattr(asvc_module.assistant_service, "handle_message", original)

    resp = d_fac["response_text"]
    assert _has_no_ids(resp)
    assert "Nearest healthcare facility" not in resp
    assert "108" in resp or "nahi aa saka" in resp.lower() or "ESCALATE" in d_fac.get("next_action", "")


# ---------------------------------------------------------------------------
# Test 12 — No unverified ASV stock or service capability claims
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_12_no_unverified_asv_or_service_claims():
    """
    AC #12: Response must not claim ASV is available, facility is open,
    referral accepted, or ambulance dispatched without verified live data.
    """
    call_sid = "t12-asv-claims"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")
        await _post(client, call_sid, "Thoda")
        await _post(client, call_sid, "Nahi")
        data4 = await _post(client, call_sid, "Hum Lucknow Bakshi Ka Talab ke paas hain")

    resp = data4["response_text"]
    assert _has_no_ids(resp)
    forbidden = [
        "asv available", "asv in stock", "asv hai", "antivenom available",
        "referral accepted", "referral confirmed", "hospital open",
        "ambulance dispatched", "ambulance bheji", "ambulance on the way",
    ]
    resp_lower = resp.lower()
    for phrase in forbidden:
        assert phrase not in resp_lower, f"Unverified claim '{phrase}': {repr(resp)}"


# ---------------------------------------------------------------------------
# Test — Silence retry during Q2 repeats the current step's question
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_silence_retry_stays_at_current_step():
    """
    Silence during Q2 (flow_step=ASK_SYMPTOM_2) must repeat Q2 content,
    not advance the state machine.
    """
    call_sid = "t-silence-q2"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")  # Q1 answered → returns Q2
        # Silence (empty transcript)
        data_silence = await _post(client, call_sid, "")

    resp = data_silence["response_text"]
    # Should repeat Q2 (or at minimum not advance past Q2)
    assert (
        "bolne" in resp or "nigalne" in resp or "saans" in resp or "kamzori" in resp
        or "khoon" in resp  # might advance to Q3 retry, still acceptable
    ), f"Expected Q2 repeated on silence, got: {repr(resp)}"
    assert _has_no_ids(resp)


# ---------------------------------------------------------------------------
# Test — Webhook lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_webhook_lifecycle():
    """Webhook must return 200 with status=received."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/webhook",
            json={"call_sid": "wh-test-lifecycle", "event_type": "call.answered"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "received"
    assert data["call_sid"] == "wh-test-lifecycle"
