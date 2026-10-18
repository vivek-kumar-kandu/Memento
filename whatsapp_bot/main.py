import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import FastAPI, Query, Request, Response, status
from fastapi.responses import PlainTextResponse
import uvicorn
from pydantic import BaseModel, Field

# Ensure current directory is in sys.path when running main.py directly
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

try:
    from config import (
        HOST,
        PORT,
        BACKEND_BASE_URL,
        ASSISTANT_ENDPOINT,
        WHATSAPP_PHONE_NUMBER_ID,
        WHATSAPP_VERIFY_TOKEN,
        GRAPH_API_VERSION,
        LOG_LEVEL,
    )
    from webhook_handler import verify_webhook, process_webhook_payload, handle_inbound_message
    from models import WhatsAppInboundMessage, WhatsAppText, WhatsAppLocation
    from session_manager import session_manager
    from meta_client import meta_client
except ImportError:
    from .config import (
        HOST,
        PORT,
        BACKEND_BASE_URL,
        ASSISTANT_ENDPOINT,
        WHATSAPP_PHONE_NUMBER_ID,
        WHATSAPP_VERIFY_TOKEN,
        GRAPH_API_VERSION,
        LOG_LEVEL,
    )
    from .webhook_handler import verify_webhook, process_webhook_payload, handle_inbound_message
    from .models import WhatsAppInboundMessage, WhatsAppText, WhatsAppLocation
    from .session_manager import session_manager
    from .meta_client import meta_client

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d | %(message)s",
)
logger = logging.getLogger("whatsapp.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Sanjeevini WhatsApp Bot Adapter on port %d...", PORT)
    logger.info("Configured Backend Endpoint: %s", ASSISTANT_ENDPOINT)
    logger.info("Meta WhatsApp Cloud API Configured: %s", meta_client.is_configured)
    yield
    logger.info("Shutting down Sanjeevini WhatsApp Bot Adapter.")


app = FastAPI(
    title="Dhwani-Sanjeevini WhatsApp Bot Adapter",
    description=(
        "Production-ready WhatsApp Cloud API adapter for Dhwani-Sanjeevini emergency response. "
        "Coordinates incoming WhatsApp user messages with the shared FastAPI backend assistant, "
        "persisting conversation and case state across turns without clinical delay."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health-check endpoint reporting adapter operational status, configuration, and session cache."""
    return {
        "status": "healthy",
        "service": "dhwani-sanjeevani-whatsapp-bot",
        "version": "1.0.0",
        "backend_base_url": BACKEND_BASE_URL,
        "assistant_endpoint": ASSISTANT_ENDPOINT,
        "meta_cloud_api": {
            "configured": meta_client.is_configured,
            "phone_number_id": WHATSAPP_PHONE_NUMBER_ID if meta_client.is_configured else "unconfigured_or_dryrun",
            "graph_api_version": GRAPH_API_VERSION,
        },
        "session_cache": {
            "active_sessions": len(session_manager._sessions),
            "processed_messages_count": len(session_manager._processed_message_ids),
        },
    }


@app.get("/webhook", tags=["Webhook"])
async def meta_webhook_verification(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    """Meta WhatsApp Cloud API Webhook Verification Endpoint.

    Called by Meta when setting up or verifying the callback URL in the Meta Developer App Dashboard.
    Must return the hub.challenge string on matching verification token with HTTP 200.
    """
    challenge_val = verify_webhook(mode=hub_mode, token=hub_verify_token, challenge=hub_challenge)
    return PlainTextResponse(content=challenge_val, status_code=status.HTTP_200_OK)


@app.post("/webhook", tags=["Webhook"])
async def meta_inbound_webhook(request: Request):
    """Meta WhatsApp Cloud API Inbound Webhook Endpoint.

    Receives message notifications and status receipts from Meta WhatsApp Cloud API.
    Processes user messages, updates persistent case and conversation sessions,
    and returns immediate HTTP 200 OK to acknowledge receipt.
    """
    try:
        payload_data = await request.json()
    except Exception as e:
        logger.error("Failed to parse JSON body from incoming webhook: %s", e)
        return Response(content="Invalid JSON", status_code=status.HTTP_400_BAD_REQUEST)

    result = await process_webhook_payload(payload_data)
    return {"status": "ok", "summary": result}


# -----------------------------------------------------------------------------
# Developer / Testing Simulation Endpoint
# -----------------------------------------------------------------------------
class SimulateMessageRequest(BaseModel):
    from_phone: str = Field(default="919876543210", description="Sender WhatsApp phone number")
    message_text: str = Field(..., description="Message text (e.g. 'Mere bhai ko saanp ne kaat liya hai')")
    message_id: Optional[str] = Field(None, description="Optional custom message ID for testing deduplication")
    latitude: Optional[float] = Field(None, description="Optional GPS latitude")
    longitude: Optional[float] = Field(None, description="Optional GPS longitude")


@app.post("/api/test/simulate-message", tags=["Testing & Simulation"])
async def simulate_incoming_message(req: SimulateMessageRequest):
    """Developer testing endpoint to simulate an incoming WhatsApp message end-to-end

    without needing live Meta Cloud API webhooks or public ngrok tunnels.
    """
    import uuid
    import time

    msg_id = req.message_id or f"sim_msg_{uuid.uuid4().hex[:12]}"
    now_ts = str(int(time.time()))

    loc_obj = None
    text_obj = None

    if req.latitude is not None and req.longitude is not None:
        loc_obj = WhatsAppLocation(latitude=req.latitude, longitude=req.longitude)
        msg_type = "location"
    else:
        text_obj = WhatsAppText(body=req.message_text)
        msg_type = "text"

    inbound_msg = WhatsAppInboundMessage(
        id=msg_id,
        from_=req.from_phone,
        timestamp=now_ts,
        type=msg_type,
        text=text_obj,
        location=loc_obj,
    )

    result = await handle_inbound_message(inbound_msg)
    return result


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
