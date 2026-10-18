from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.schemas.common import Channel
from app.schemas.facility import FacilityNearbyItem
from app.schemas.case import ReferralInfo


class GPSLocationPayload(BaseModel):
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Client device GPS latitude in decimal degrees (-90 to 90)",
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Client device GPS longitude in decimal degrees (-180 to 180)",
    )
    accuracy_m: Optional[float] = Field(
        None,
        ge=0.0,
        description="Reported client-device GPS horizontal accuracy in meters (informational metadata, not proof of location authenticity)",
    )
    village: Optional[str] = Field(None, description="Optional user-reported village, town, or subdistrict")
    landmark: Optional[str] = Field(None, description="Optional user-reported landmark or address context")

    @field_validator("latitude", "longitude", "accuracy_m", mode="after")
    @classmethod
    def validate_finite(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            import math
            if math.isnan(v) or math.isinf(v):
                raise ValueError("Location numeric values must be finite numbers, not NaN or Infinity")
        return v

    @model_validator(mode="after")
    def check_coords_pair(self) -> "GPSLocationPayload":
        has_lat = self.latitude is not None
        has_lon = self.longitude is not None
        if has_lat != has_lon:
            raise ValueError("Both latitude and longitude must be provided together.")
        return self

    model_config = ConfigDict(extra="allow")


class AssistantMessageRequest(BaseModel):
    channel: Channel = Field(default=Channel.IVR, description="Access channel (IVR, WHATSAPP, FLUTTER)")
    conversation_id: Optional[str] = Field(None, description="Existing conversation session ID or None for new session")
    message: str = Field(..., min_length=1, description="Caller utterance, user text, or transcript")
    case_id: Optional[str] = Field(None, description="Active emergency case ID if known")
    location: Optional[GPSLocationPayload] = Field(
        None,
        description="Optional GPS coordinates (e.g. {'latitude': 26.8467, 'longitude': 80.9462, 'accuracy_m': 15.0}) or location context",
    )
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
