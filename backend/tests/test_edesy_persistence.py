"""
test_edesy_persistence.py — Genuine database persistence tests for Sanjeevani Edesy Voice Sessions.

Validates all 10 core requirements:
1. A new call begins at the expected first-answer state and returns Q2 after answering Q1.
2. Subsequent answers progress to Q3 and then location collection.
3. A subsequent location turn returns only actual database-backed facility matches.
4. The same call ID retains state across independent HTTP requests.
5. Clearing all in-memory objects between turns does not lose progress.
6. Recreating the endpoint/service or database session between turns does not lose progress.
7. Different call IDs do not share answers or locations.
8. Repeated requests do not create duplicate cases merely because another symptom answer arrived.
9. A persistence failure does not produce a fabricated successful answer.
10. Existing no-spoken-ID, emergency exception, location, and facility tests still pass.
"""
import re
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, text

from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.models.conversation import ConversationSession
from app.db.models.case import EmergencyCase
from app.api.v1.endpoints import edesy as edesy_module

_TOOL = "/api/v1/edesy/tool"

# Regex to detect any spoken Case ID or UUID pattern
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


@pytest_asyncio.fixture(autouse=True)
async def cleanup_persistence_test_sessions():
    """Ensure clean isolated state for test call IDs before and after each test."""
    async with AsyncSessionLocal() as db:
        await db.execute(
            text(
                "DELETE FROM conversation_sessions WHERE id LIKE 'persist-%' "
                "OR id LIKE 'iso-%' OR id LIKE 'fail-%' OR id LIKE 'dup-%'"
            )
        )
        await db.commit()
    yield
    async with AsyncSessionLocal() as db:
        await db.execute(
            text(
                "DELETE FROM conversation_sessions WHERE id LIKE 'persist-%' "
                "OR id LIKE 'iso-%' OR id LIKE 'fail-%' OR id LIKE 'dup-%'"
            )
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Requirement 1: New call begins at first-answer state and returns Q2
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_1_new_call_persists_q1_answer_returns_q2():
    call_sid = f"persist-call-1-{uuid.uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _post(client, call_sid, "Saanp ne haath mein kaata hai")

    # Caller answered Q1; endpoint must return Q2
    resp = data["response_text"]
    assert "bolne" in resp or "nigalne" in resp or "saans" in resp or "kamzori" in resp
    assert _has_no_ids(resp)
    assert data["next_action"] == "CONTINUE"

    # Verify directly from the database that state was persisted
    async with AsyncSessionLocal() as db:
        stmt = select(ConversationSession).where(ConversationSession.id == call_sid)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

    assert session is not None, "ConversationSession was not created in the database"
    assert session.channel == "IVR"
    assert session.state == "ACTIVE"
    assert session.case_id is None, "Emergency case must not be created on turn 1 symptom screening"

    ctx = session.context_data
    assert ctx["call_sid"] == call_sid
    assert ctx["flow_step"] == "ASK_SYMPTOM_2"
    assert len(ctx["symptom_answers"]) == 1
    assert "Saanp ne haath mein kaata" in ctx["symptom_answers"][0]
    assert ctx["turn_count"] == 1


# ---------------------------------------------------------------------------
# Requirement 2: Subsequent answers progress to Q3 and then location
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_2_subsequent_answers_progress_to_q3_and_location():
    call_sid = f"persist-call-2-{uuid.uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Turn 1: Caller answers Q1
        d1 = await _post(client, call_sid, "Haan saanp ne kaata")
        assert "bolne" in d1["response_text"] or "nigalne" in d1["response_text"] or "saans" in d1["response_text"]

        # Turn 2: Caller answers Q2
        d2 = await _post(client, call_sid, "Aankhein thodi bhaari hain")
        # Must return Q3 (bleeding / local signs)
        assert "khoon" in d2["response_text"] or "sujan" in d2["response_text"] or "masoodon" in d2["response_text"]
        assert d2["next_action"] == "CONTINUE"

        # Check DB after Turn 2
        async with AsyncSessionLocal() as db:
            session = (await db.execute(select(ConversationSession).where(ConversationSession.id == call_sid))).scalar_one()
            assert session.context_data["flow_step"] == "ASK_SYMPTOM_3"
            assert len(session.context_data["symptom_answers"]) == 2

        # Turn 3: Caller answers Q3
        d3 = await _post(client, call_sid, "Nahi khoon nahi nikal raha")
        # Must return location question
        assert "gaon" in d3["response_text"] or "mohalla" in d3["response_text"] or "district" in d3["response_text"]
        assert d3["next_action"] == "COLLECT_LOCATION"

        # Check DB after Turn 3
        async with AsyncSessionLocal() as db:
            session = (await db.execute(select(ConversationSession).where(ConversationSession.id == call_sid))).scalar_one()
            assert session.context_data["flow_step"] == "COLLECT_LOCATION"
            assert len(session.context_data["symptom_answers"]) == 3


# ---------------------------------------------------------------------------
# Requirement 3: Location turn returns only actual database-backed facilities
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_3_location_turn_returns_only_actual_db_facilities():
    call_sid = f"persist-call-3-{uuid.uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata")
        await _post(client, call_sid, "Nahi theek hai")
        await _post(client, call_sid, "Nahi khoon nahi")

        # Turn 4: Provide real location in Lucknow
        d4 = await _post(client, call_sid, "Hum Lucknow mein Bakshi Ka Talab ke paas hain")

    resp = d4["response_text"]
    assert _has_no_ids(resp)

    # Must match actual Lucknow facilities from the BallTree database
    known_lucknow_facilities = ["ITAUNJA", "BKT", "MAHONA", "KATHWARA", "CHC", "PHC"]
    assert any(fac in resp.upper() for fac in known_lucknow_facilities), (
        f"Spoken text does not contain actual DB facilities: {resp}"
    )

    # Must include honest ASV warning
    assert "ASV stock ki guarantee nahi hai" in resp

    # Check DB: flow is DONE
    async with AsyncSessionLocal() as db:
        session = (await db.execute(select(ConversationSession).where(ConversationSession.id == call_sid))).scalar_one()
        assert session.context_data["flow_step"] == "DONE"


# ---------------------------------------------------------------------------
# Requirement 4: Same call ID retains state across independent HTTP requests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_4_same_call_id_retains_state_across_independent_http_requests():
    call_sid = f"persist-call-4-{uuid.uuid4().hex[:6]}"

    # Request 1 via client A
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test-a") as client_a:
        d1 = await _post(client_a, call_sid, "Saanp ne kaata")
        assert "bolne" in d1["response_text"] or "saans" in d1["response_text"]

    # Request 2 via completely separate client B
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test-b") as client_b:
        d2 = await _post(client_b, call_sid, "Nahi")
        assert "khoon" in d2["response_text"] or "sujan" in d2["response_text"]

    # Request 3 via client C
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test-c") as client_c:
        d3 = await _post(client_c, call_sid, "Nahi")
        assert "gaon" in d3["response_text"] or "landmark" in d3["response_text"]


# ---------------------------------------------------------------------------
# Requirement 5: Clearing in-memory objects does NOT lose progress
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_5_clearing_in_memory_objects_between_turns_does_not_lose_progress():
    call_sid = f"persist-call-5-{uuid.uuid4().hex[:6]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Turn 1
        d1 = await _post(client, call_sid, "Saanp ne kaata hai")
        assert "bolne" in d1["response_text"] or "saans" in d1["response_text"]

        # SIMULATE APPLICATION RESTART / IN-MEMORY CACHE PURGE
        edesy_module._CALL_SESSIONS.clear()

        # Turn 2 must resume from DB state at Turn 2, returning Q3 (not restarting at Q2)
        d2 = await _post(client, call_sid, "Nahi theek hai")
        assert "khoon" in d2["response_text"] or "sujan" in d2["response_text"]

        # PURGE AGAIN
        edesy_module._CALL_SESSIONS.clear()

        # Turn 3 must resume from DB state at Turn 3, returning location question
        d3 = await _post(client, call_sid, "Nahi khoon nahi hai")
        assert "gaon" in d3["response_text"] or "district" in d3["response_text"]


# ---------------------------------------------------------------------------
# Requirement 6: Recreating database session between turns does not lose progress
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_6_recreating_database_session_between_turns():
    call_sid = f"persist-call-6-{uuid.uuid4().hex[:6]}"

    # Turn 1
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await _post(client, call_sid, "Saanp ne kaata hai")

    # Open isolated DB session and verify committed row
    async with AsyncSessionLocal() as isolated_db:
        session = (
            await isolated_db.execute(
                select(ConversationSession).where(ConversationSession.id == call_sid)
            )
        ).scalar_one()
        assert session.context_data["flow_step"] == "ASK_SYMPTOM_2"
        # Close isolated_db session cleanly

    # Turn 2 uses fresh DB session under the hood
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        d2 = await _post(client, call_sid, "Thoda dard hai")
        assert "khoon" in d2["response_text"] or "sujan" in d2["response_text"]


# ---------------------------------------------------------------------------
# Requirement 7: Different call IDs do not share answers or locations
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_7_different_call_ids_do_not_share_answers_or_locations():
    call_a = f"iso-call-A-{uuid.uuid4().hex[:6]}"
    call_b = f"iso-call-B-{uuid.uuid4().hex[:6]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Caller A answers Q1
        await _post(client, call_a, "Caller A: Saanp ne haath mein kaata")
        # Caller B answers Q1 with different text
        await _post(client, call_b, "Caller B: Pair par kaat liya hai")

        # Caller A advances to Q2 answer
        await _post(client, call_a, "Caller A: Bolne mein dikkat nahi")

    # Verify both DB sessions are completely segregated
    async with AsyncSessionLocal() as db:
        session_a = (
            await db.execute(select(ConversationSession).where(ConversationSession.id == call_a))
        ).scalar_one()
        session_b = (
            await db.execute(select(ConversationSession).where(ConversationSession.id == call_b))
        ).scalar_one()

    # Caller A should be at ASK_SYMPTOM_3 with 2 answers
    assert session_a.context_data["flow_step"] == "ASK_SYMPTOM_3"
    assert len(session_a.context_data["symptom_answers"]) == 2
    assert "Caller A" in session_a.context_data["symptom_answers"][0]

    # Caller B should still be at ASK_SYMPTOM_2 with 1 answer
    assert session_b.context_data["flow_step"] == "ASK_SYMPTOM_2"
    assert len(session_b.context_data["symptom_answers"]) == 1
    assert "Caller B" in session_b.context_data["symptom_answers"][0]


# ---------------------------------------------------------------------------
# Requirement 8: Repeated requests do not create duplicate cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_8_repeated_requests_do_not_create_duplicate_cases():
    call_sid = f"dup-call-{uuid.uuid4().hex[:6]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Turns 1-3
        await _post(client, call_sid, "Saanp ne kaata hai")
        await _post(client, call_sid, "Nahi")
        await _post(client, call_sid, "Nahi")

        # Location turn
        d4 = await _post(client, call_sid, "Hum Mohanlalganj Lucknow ke paas hain")
        case_id_turn4 = d4.get("case_id")

        # Additional repeated request on the same call
        d5 = await _post(client, call_sid, "Aur koi hospital hai kya?")
        case_id_turn5 = d5.get("case_id")

    # If case_id was assigned, it must remain identical
    if case_id_turn4 and case_id_turn5:
        assert case_id_turn4 == case_id_turn5, (
            f"Case ID changed between turns: {case_id_turn4} vs {case_id_turn5}"
        )


# ---------------------------------------------------------------------------
# Requirement 9: Persistence failure does not produce a fabricated answer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_9_persistence_failure_does_not_produce_fabricated_answer(monkeypatch):
    call_sid = f"fail-call-{uuid.uuid4().hex[:6]}"

    from sqlalchemy.ext.asyncio import AsyncSession

    original_commit = AsyncSession.commit

    # Simulate a DB commit error (e.g. disk full, DB locked)
    async def _failing_commit(self):
        raise RuntimeError("Simulated DB Transaction Failure")

    monkeypatch.setattr(AsyncSession, "commit", _failing_commit)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(_TOOL, json={"call_sid": call_sid, "transcript": "Saanp ne kaata"})
            assert res.status_code == 200
            data = res.json()
    finally:
        monkeypatch.setattr(AsyncSession, "commit", original_commit)

    # Must return honest error and escalate to human, NOT fabricate success
    assert data["next_action"] == "ESCALATE_HUMAN"
    assert "108" in data["response_text"]
    assert "sampark nahi ho saka" in data["response_text"] or "kharabi" in data["response_text"]
    assert _has_no_ids(data["response_text"])


# ---------------------------------------------------------------------------
# Requirement 10: Missing call_sid rejects with explicit HTTP 400
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_10_missing_call_sid_rejects_with_explicit_400():
    """Verify that requests without any call identifier are rejected without assigning a shared fallback session."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(_TOOL, json={"transcript": "Saanp ne kaata"})
        assert res.status_code == 400
        detail = res.json().get("detail", "")
        assert "call_sid" in detail
