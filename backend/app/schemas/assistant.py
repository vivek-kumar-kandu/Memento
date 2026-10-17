from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import Channel
from app.schemas.facility import FacilityNearbyItem
from app.schemas.case import ReferralInfo


class AssistantMessageRequest(BaseModel):
    channel: Channel = Field(default=Channel.IVR, description="Access channel (IVR, WHATSAPP, FLUTTER)")
    conversation_id: Optional[str] = Field(None, description="Existing conversation session ID or None for new session")
    message: str = Field(..., min_length=1, description="Caller utterance, user text, or transcript")
    case_id: Optional[str] = Field(None, description="Active emergency case ID if known")
    location: Optional[Dict[str, Any]] = Field(None, description="Optional GPS coordinates or location context")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional conversation context from caller/app")


class AssistantMessageResponse(BaseModel):
    conversation_id: str = Field(..., description="Stable conversation session ID")
    intent: str = Field(..., description="Predicted or detected intent name")
    intent_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of classification")
    response_text: str = Field(..., description="Actionable response text to read or display")
    case_id: Optional[str] = Field(None, description="Associated emergency case ID")
    case_status: Optional[str] = Field(None, description="Current lifecycle status of the case")
    next_action: str = Field(..., description="Next operational or clinical step")
    missing_information: List[str] = Field(default_factory=list, description="Missing required fields to collect")
    nearby_facilities: Optional[List[FacilityNearbyItem]] = Field(None, description="List of closest facilities if location is known")
    referral: Optional[ReferralInfo] = Field(None, description="Active referral status if initiated")
    safety_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Clinician-reviewed safety guidance and ASV verification caveats",
    )

    model_config = ConfigDict(from_attributes=True)
