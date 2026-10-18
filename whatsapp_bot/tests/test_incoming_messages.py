import pytest
from fastapi.testclient import TestClient
from webhook_handler import process_webhook_payload
from session_manager import session_manager


@pytest.mark.anyio
async def test_process_inbound_text_message(mock_backend):
    """Test full parsing of inbound WhatsApp text webhook."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "15550234567", "phone_number_id": "123456789"},
                            "contacts": [{"profile": {"name": "Ramesh"}, "wa_id": "919876543210"}],
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAEhgWM0VCMDM0QTY5ODJCMUI3QzQ4MEYyOAA=",
                                    "timestamp": "1729228800",
                                    "type": "text",
                                    "text": {"body": "Mere bhai ko saanp ne kaat liya hai emergency"},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    result = await process_webhook_payload(payload, backend_cli=mock_backend)
    assert result["processed_count"] == 1
    res = result["results"][0]
    assert res["status"] == "processed"
    assert res["sender"] == "919876543210"
    assert res["case_id"] == "DS-2026-TEST01"
    assert "DS-2026-TEST01" in res["reply_preview"]

    # Verify session was persisted
    sess = session_manager.get_session("919876543210")
    assert sess is not None
    assert sess.case_id == "DS-2026-TEST01"
    assert sess.conversation_id == "test-conv-uuid-1234"


@pytest.mark.anyio
async def test_process_inbound_location_message(mock_backend):
    """Test parsing of inbound WhatsApp GPS location pin message."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.LOCATION_MSG_001",
                                    "timestamp": "1729228810",
                                    "type": "location",
                                    "location": {
                                        "latitude": 26.8467,
                                        "longitude": 80.9462,
                                        "name": "Bakshi Ka Talab",
                                        "address": "Lucknow, UP",
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    result = await process_webhook_payload(payload, backend_cli=mock_backend)
    assert result["processed_count"] == 1
    res = result["results"][0]
    assert res["status"] == "processed"

    # Verify backend received GPS location payload
    assert len(mock_backend.call_history) == 1
    sent_loc = mock_backend.call_history[0]["location"]
    assert sent_loc is not None
    assert sent_loc.latitude == 26.8467
    assert sent_loc.longitude == 80.9462


@pytest.mark.anyio
async def test_delivery_status_receipts_ignored():
    """Verify Meta status updates (sent, delivered, read) do NOT create cases or trigger user replies."""
    status_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "statuses": [
                                {
                                    "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAEhgWM0VCMDM0QTY5ODJCMUI3QzQ4MEYyOAA=",
                                    "status": "delivered",
                                    "timestamp": "1729228805",
                                    "recipient_id": "919876543210",
                                },
                                {
                                    "id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAEhgWM0VCMDM0QTY5ODJCMUI3QzQ4MEYyOAA=",
                                    "status": "read",
                                    "timestamp": "1729228806",
                                    "recipient_id": "919876543210",
                                },
                            ],
                        },
                    }
                ],
            }
        ],
    }

    result = await process_webhook_payload(status_payload)
    assert result["processed_count"] == 1
    res = result["results"][0]
    assert res["status"] == "ignored_delivery_receipt"
    assert res["count"] == 2


@pytest.mark.anyio
async def test_message_deduplication(mock_backend):
    """Verify that retried Meta webhooks with identical message ID are deduplicated and not reprocessed."""
    raw_msg = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.DUPLICATE_TEST_ID_001",
                                    "timestamp": "1729228800",
                                    "type": "text",
                                    "text": {"body": "Saanp ne kaat liya hai"},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    # First delivery: processed
    res1 = await process_webhook_payload(raw_msg, backend_cli=mock_backend)
    assert res1["results"][0]["status"] == "processed"
    assert len(mock_backend.call_history) == 1

    # Second delivery with identical message ID (Meta webhook retry): ignored
    res2 = await process_webhook_payload(raw_msg, backend_cli=mock_backend)
    assert res2["results"][0]["status"] == "duplicate_ignored"
    # Backend was NOT called a second time
    assert len(mock_backend.call_history) == 1


def test_post_webhook_bad_json(client: TestClient):
    """Verify invalid JSON returns HTTP 400 Bad Request."""
    resp = client.post("/webhook", content="not-a-valid-json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
