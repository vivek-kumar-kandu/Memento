import pytest
from fastapi.testclient import TestClient
from webhook_handler import handle_inbound_message
from models import WhatsAppInboundMessage, WhatsAppText
from session_manager import session_manager


@pytest.mark.anyio
async def test_three_turn_emergency_flow(mock_backend):
    """Test the complete 3-turn emergency workflow specified in the integration specification:

    Turn 1: Emergency report -> Creates case, captures conversation_id & case_id, asks for location.
    Turn 2: Location response -> Reuses IDs, returns nearby facilities with UNKNOWN ASV, PENDING referral.
    Turn 3: Follow-up question -> Continues same case without creating duplicate.
    """
    sender = "919876543210"

    # -------------------------------------------------------------------------
    # TURN 1: Emergency Report
    # -------------------------------------------------------------------------
    msg1 = WhatsAppInboundMessage(
        id="wamid.TURN_001",
        from_=sender,
        timestamp="1729228800",
        type="text",
        text=WhatsAppText(body="Mere bhai ko saanp ne kaat liya hai, jaldi madad chahiye."),
    )

    turn1_result = await handle_inbound_message(msg1, backend_cli=mock_backend)
    assert turn1_result["status"] == "processed"
    assert turn1_result["case_id"] == "DS-2026-TEST01"
    assert turn1_result["conversation_id"] == "test-conv-uuid-1234"
    assert "DS-2026-TEST01" in turn1_result["reply_preview"]

    # Verify session state after Turn 1
    sess_after_1 = session_manager.get_session(sender)
    assert sess_after_1 is not None
    assert sess_after_1.case_id == "DS-2026-TEST01"
    assert sess_after_1.conversation_id == "test-conv-uuid-1234"
    assert sess_after_1.message_count == 1

    # -------------------------------------------------------------------------
    # TURN 2: Location Reply
    # -------------------------------------------------------------------------
    msg2 = WhatsAppInboundMessage(
        id="wamid.TURN_002",
        from_=sender,
        timestamp="1729228840",
        type="text",
        text=WhatsAppText(body="Hum Lucknow mein Bakshi Ka Talab ke paas hain."),
    )

    turn2_result = await handle_inbound_message(msg2, backend_cli=mock_backend)
    assert turn2_result["status"] == "processed"
    # Case ID and conversation ID MUST be preserved from Turn 1
    assert turn2_result["case_id"] == "DS-2026-TEST01"
    assert turn2_result["conversation_id"] == "test-conv-uuid-1234"

    # Verify backend was called with conversation_id and case_id from Turn 1
    assert len(mock_backend.call_history) == 2
    turn2_backend_call = mock_backend.call_history[1]
    assert turn2_backend_call["conversation_id"] == "test-conv-uuid-1234"
    assert turn2_backend_call["case_id"] == "DS-2026-TEST01"

    # Verify session count updated
    sess_after_2 = session_manager.get_session(sender)
    assert sess_after_2.message_count == 2

    # -------------------------------------------------------------------------
    # TURN 3: Follow-up Question
    # -------------------------------------------------------------------------
    msg3 = WhatsAppInboundMessage(
        id="wamid.TURN_003",
        from_=sender,
        timestamp="1729228880",
        type="text",
        text=WhatsAppText(body="Ab kya karna chahiye?"),
    )

    turn3_result = await handle_inbound_message(msg3, backend_cli=mock_backend)
    assert turn3_result["status"] == "processed"
    # Same case ID and conversation ID preserved
    assert turn3_result["case_id"] == "DS-2026-TEST01"
    assert turn3_result["conversation_id"] == "test-conv-uuid-1234"

    # Verify backend called with same IDs
    assert len(mock_backend.call_history) == 3
    turn3_backend_call = mock_backend.call_history[2]
    assert turn3_backend_call["conversation_id"] == "test-conv-uuid-1234"
    assert turn3_backend_call["case_id"] == "DS-2026-TEST01"

    sess_after_3 = session_manager.get_session(sender)
    assert sess_after_3.message_count == 3


def test_simulation_endpoint_end_to_end(client: TestClient):
    """Test POST /api/test/simulate-message developer endpoint."""
    payload = {
        "from_phone": "919123456789",
        "message_text": "Saanp ne kaat liya hai emergency",
        "message_id": "sim_test_001",
    }
    resp = client.post("/api/test/simulate-message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processed"
    assert data["sender"] == "919123456789"
    assert "reply_preview" in data
