from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EdesyWebhookEvent(BaseModel):
    """Schema for asynchronous Edesy call lifecycle webhook events."""
    event_type: str = Field(..., description="Lifecycle event: call.initiated, call.answered, call.ended, etc.")
    call_sid: str = Field(..., description="Unique telephony call identifier from Edesy")
    from_number: Optional[str] = Field(default=None, description="Caller phone number")
    to_number: Optional[str] = Field(default=None, description="Dialed IVR helpline number")
    recording_url: Optional[str] = Field(default=None, description="Audio recording URL if available")
    duration_seconds: Optional[int] = Field(default=None, description="Call duration in seconds")
    timestamp: Optional[str] = Field(default=None, description="Event timestamp")


class EdesyToolRequest(BaseModel):
    """
    Schema for synchronous in-conversation tool calls from Edesy's voice agent.
    Accepts both standard and common telephony parameter naming.
    """
    call_sid: Optional[str] = Field(default=None, description="Call session identifier")
    call_id: Optional[str] = Field(default=None, description="Alternative field for call identifier")
    session_id: Optional[str] = Field(default=None, description="Alternative field for session identifier")
    conversation_id: Optional[str] = Field(default=None, description="Alternative field for conversation identifier")
    transcript: Optional[str] = Field(default=None, description="Transcribed caller utterance from Edesy STT")
    message: Optional[str] = Field(default=None, description="Alternative field for transcript")
    caller_phone: Optional[str] = Field(default=None, description="Caller telephone number")
    language: Optional[str] = Field(default="en", description="Language code (en, hi, etc.)")


class EdesyToolResponse(BaseModel):
    """Schema for synchronous response returned to Edesy voice bot."""
    response_text: str = Field(..., description="Spoken prompt for Edesy TTS to synthesize")
    next_action: str = Field(..., description="Conversation action: CONTINUE, COLLECT_LOCATION, ESCALATE_HUMAN, END_CALL")
    end_call: bool = Field(default=False, description="Whether telephony engine should hang up")
    conversation_id: Optional[str] = Field(default=None, description="Backend conversation ID")
    case_id: Optional[str] = Field(default=None, description="Backend emergency case ID")
    language: Optional[str] = Field(default="hindi", description="Detected caller language (hindi, hinglish, bhojpuri)")
