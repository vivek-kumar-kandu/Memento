import pytest
from session_manager import SessionManager


def test_session_lifecycle_and_persistence(tmp_path):
    """Verify session data persists across SessionManager instances (simulating server restart)."""
    storage_file = tmp_path / "sessions_test.json"
    mgr1 = SessionManager(storage_path=str(storage_file))

    sender = "919876543210"
    # Create initial session
    sess = mgr1.get_or_create_session(sender)
    assert sess.whatsapp_id == sender
    assert sess.conversation_id is None
    assert sess.case_id is None

    # Update session with backend IDs
    mgr1.update_session(
        whatsapp_id=sender,
        conversation_id="conv-1111-2222-3333",
        case_id="DS-2026-PERSIST01",
        last_message_id="msg-abc-001",
        last_user_message="Emergency snakebite",
    )

    assert mgr1.is_message_processed("msg-abc-001") is True
    assert mgr1.is_message_processed("msg-abc-002") is False

    # Simulate restart: create brand new SessionManager reading same file
    mgr2 = SessionManager(storage_path=str(storage_file))
    reloaded_sess = mgr2.get_session(sender)

    assert reloaded_sess is not None
    assert reloaded_sess.conversation_id == "conv-1111-2222-3333"
    assert reloaded_sess.case_id == "DS-2026-PERSIST01"
    assert reloaded_sess.last_message_id == "msg-abc-001"
    assert reloaded_sess.message_count == 1
    assert mgr2.is_message_processed("msg-abc-001") is True


def test_multiple_senders_isolation(tmp_path):
    """Verify different WhatsApp senders maintain completely isolated sessions and cases."""
    storage_file = tmp_path / "sessions_multi.json"
    mgr = SessionManager(storage_path=str(storage_file))

    user_a = "919876543210"
    user_b = "919999888877"

    mgr.update_session(whatsapp_id=user_a, conversation_id="conv-user-a", case_id="CASE-A")
    mgr.update_session(whatsapp_id=user_b, conversation_id="conv-user-b", case_id="CASE-B")

    sess_a = mgr.get_session(user_a)
    sess_b = mgr.get_session(user_b)

    assert sess_a.conversation_id == "conv-user-a"
    assert sess_a.case_id == "CASE-A"

    assert sess_b.conversation_id == "conv-user-b"
    assert sess_b.case_id == "CASE-B"
