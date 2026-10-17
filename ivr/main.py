import sys
from pathlib import Path
from fastapi import FastAPI
import uvicorn

# Ensure the ivr directory is in sys.path when running main.py directly
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
from fastapi import APIRouter, FastAPI, Request
from pydantic import BaseModel, Field
import uvicorn

try:
    from config import HOST, PORT, BACKEND_BASE_URL, ASSISTANT_ENDPOINT
    from conversation import ConversationController, SessionStore
    from backend_client import BackendClient
    from edesy_adapter import router as edesy_router
except ImportError:
    from .config import HOST, PORT, BACKEND_BASE_URL, ASSISTANT_ENDPOINT
    from .conversation import ConversationController, SessionStore
    from .backend_client import BackendClient
    from .edesy_adapter import router as edesy_router


# Shared controller instance
backend_client = BackendClient()
session_store = SessionStore()
conversation_controller = ConversationController(
    backend_client=backend_client, session_store=session_store
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.conversation_controller = conversation_controller
    yield


app = FastAPI(
    title="Sanjeevani IVR Adapter",
    description="Adapter service interfacing Edesy Telephony/Voice AI with Dhwani-Sanjeevani FastAPI Backend.",
    version="0.1.0",
    lifespan=lifespan,
)

# Store controller in state immediately for sync access
app.state.conversation_controller = conversation_controller


@app.get("/health", tags=["Health"])
async def health_check():
    """Health-check endpoint to verify adapter status and configuration."""
    return {
        "status": "ok",
        "service": "sanjeevani-ivr-adapter",
        "version": "0.1.0",
        "backend_base_url_configured": bool(BACKEND_BASE_URL),
        "assistant_endpoint": ASSISTANT_ENDPOINT,
    }


# Direct telephony-agnostic router (used for testing and direct integration)
ivr_router = APIRouter(prefix="/api/v1/ivr", tags=["Direct IVR Call Control"])


class InboundCallRequest(BaseModel):
    session_id: str = Field(..., description="Unique call session ID")
    caller_phone: Optional[str] = Field(default=None, description="Caller phone number")
    language: Optional[str] = Field(default="en", description="Language code")


class UtteranceRequest(BaseModel):
    session_id: str = Field(..., description="Unique call session ID")
    transcript: Optional[str] = Field(default=None, description="Transcribed caller speech")
    caller_phone: Optional[str] = Field(default=None, description="Caller phone number")


class EndCallRequest(BaseModel):
    session_id: str = Field(..., description="Unique call session ID")


@ivr_router.post("/call/inbound")
async def call_inbound(payload: InboundCallRequest, request: Request) -> Dict[str, Any]:
    controller: ConversationController = request.app.state.conversation_controller
    return controller.start_call(
        session_id=payload.session_id,
        caller_phone=payload.caller_phone,
        language=payload.language,
    )


@ivr_router.post("/call/utterance")
async def call_utterance(payload: UtteranceRequest, request: Request) -> Dict[str, Any]:
    controller: ConversationController = request.app.state.conversation_controller
    return await controller.process_utterance(
        session_id=payload.session_id,
        transcript=payload.transcript,
        caller_phone=payload.caller_phone,
    )


@ivr_router.post("/call/end")
async def call_end(payload: EndCallRequest, request: Request) -> Dict[str, Any]:
    controller: ConversationController = request.app.state.conversation_controller
    return controller.end_call(session_id=payload.session_id)


# Include routers
app.include_router(ivr_router)
app.include_router(edesy_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)

