import logging
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

try:
    from config import WHATSAPP_VERIFY_TOKEN
    from models import (
        MetaWebhookPayload,
        WhatsAppInboundMessage,
        GPSLocationPayload,
        AssistantMessageResponse,
    )
    from session_manager import session_manager
    from backend_client import backend_client
    from meta_client import meta_client
except ImportError:
    from .config import WHATSAPP_VERIFY_TOKEN
    from .models import (
        MetaWebhookPayload,
        WhatsAppInboundMessage,
        GPSLocationPayload,
        AssistantMessageResponse,
    )
    from .session_manager import session_manager
    from .backend_client import backend_client
    from .meta_client import meta_client

logger = logging.getLogger("whatsapp.webhook_handler")


def verify_webhook(mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> str:
    """Verifies incoming Meta webhook subscription challenge.

    Returns the challenge string if token matches, otherwise raises HTTP 403.
    """
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("Meta webhook verification challenge succeeded.")
        return challenge or ""
    logger.warning("Meta webhook verification failed: mode=%s, token mismatch", mode)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch or invalid mode",
    )


async def handle_inbound_message(
    msg: WhatsAppInboundMessage,
    backend_cli=None,
    meta_cli=None,
    sess_mgr=None,
) -> Dict[str, Any]:
    """Processes a single inbound WhatsApp message end-to-end:

    1. Checks message deduplication.
    2. Extracts text or GPS location payload.
    3. Retrieves persistent conversation_id and case_id.
    4. Calls backend assistant endpoint.
    5. Updates session with returned IDs.
    6. Sends formatted reply to user.
    """
    backend = backend_cli or backend_client
    meta = meta_cli or meta_client
    sessions = sess_mgr or session_manager

    # 1. Deduplication guard
    if sessions.is_message_processed(msg.id):
        logger.info("Duplicate webhook event ignored for message ID: %s", msg.id)
        return {"status": "duplicate_ignored", "message_id": msg.id}

    sender_id = msg.from_
    user_text = ""
    location_payload: Optional[GPSLocationPayload] = None

    # 2. Extract content based on message type
    if msg.type == "text" and msg.text:
        user_text = msg.text.body.strip()
    elif msg.type == "location" and msg.location:
        loc = msg.location
        location_payload = GPSLocationPayload(
            latitude=loc.latitude,
            longitude=loc.longitude,
            village=loc.name,
            landmark=loc.address,
        )
        user_text = f"Location pin shared: {loc.latitude:.4f}, {loc.longitude:.4f}"
        if loc.name or loc.address:
            user_text += f" ({loc.name or ''} {loc.address or ''})".strip()
    elif msg.type == "interactive" and msg.interactive and msg.interactive.button_reply:
        user_text = msg.interactive.button_reply.title.strip()
    else:
        # Unsupported media or empty payload: prompt caller safely
        user_text = "Emergency report (unsupported media format)"
        logger.info("Received non-text message type '%s' from %s", msg.type, sender_id)

    if not user_text:
        user_text = "Emergency assistance needed"

    # 3. Retrieve user session state (maintaining conversation and case continuity)
    session = sessions.get_or_create_session(sender_id)
    conv_id = session.conversation_id
    case_id = session.case_id

    logger.info(
        "Processing WhatsApp message from %s (msg_id: %s, conv_id: %s, case_id: %s): %s",
        sender_id,
        msg.id,
        conv_id,
        case_id,
        user_text[:80],
    )

    # 4. Dispatch to backend assistant endpoint
    backend_resp: AssistantMessageResponse = await backend.send_message(
        message=user_text,
        conversation_id=conv_id,
        case_id=case_id,
        location=location_payload,
        context={"whatsapp_id": sender_id, "message_id": msg.id},
    )

    # 5. Persist returned conversation_id and case_id into session store
    updated_session = sessions.update_session(
        whatsapp_id=sender_id,
        conversation_id=backend_resp.conversation_id,
        case_id=backend_resp.case_id or case_id,
        last_message_id=msg.id,
        last_user_message=user_text,
    )

    # 6. Format and dispatch outbound message to user
    formatted_reply = meta.format_whatsapp_message(backend_resp)
    send_result = await meta.send_text_message(to_phone=sender_id, text_body=formatted_reply)

    return {
        "status": "processed",
        "sender": sender_id,
        "message_id": msg.id,
        "conversation_id": updated_session.conversation_id,
        "case_id": updated_session.case_id,
        "intent": backend_resp.intent,
        "reply_preview": formatted_reply[:100],
        "meta_dispatch": send_result,
    }


async def process_webhook_payload(
    payload_data: Dict[str, Any],
    backend_cli=None,
    meta_cli=None,
    sess_mgr=None,
) -> Dict[str, Any]:
    """Parses incoming Meta WhatsApp webhook payload.

    Distinguishes messages from delivery status receipts, processes messages, and handles errors.
    """
    entries = payload_data.get("entry", [])
    results: List[Dict[str, Any]] = []

    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})

            # 1. Ignore delivery/read status updates (do not treat as user messages)
            statuses = value.get("statuses", [])
            if statuses:
                for st in statuses:
                    logger.debug("Received message status update: id=%s, status=%s", st.get("id"), st.get("status"))
                results.append({"status": "ignored_delivery_receipt", "count": len(statuses)})
                continue

            # 2. Process incoming user messages
            messages = value.get("messages", [])
            for raw_msg in messages:
                try:
                    inbound_msg = WhatsAppInboundMessage(**raw_msg)
                    res = await handle_inbound_message(
                        msg=inbound_msg,
                        backend_cli=backend_cli,
                        meta_cli=meta_cli,
                        sess_mgr=sess_mgr,
                    )
                    results.append(res)
                except Exception as ex:
                    logger.error("Error processing inbound message %s: %s", raw_msg.get("id"), ex, exc_info=True)
                    results.append({"status": "error", "message_id": raw_msg.get("id"), "error": str(ex)})

    return {"processed_count": len(results), "results": results}
