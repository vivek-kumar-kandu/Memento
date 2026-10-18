from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

# Clinician-approved emergency fallback guidance (never delays referral or invents diagnoses)
EMERGENCY_FALLBACK_TEXT = (
    "🚨 *EMERGENCY ADVISORY (SUSPECTED SNAKEBITE)* 🚨\n\n"
    "1. Keep the patient completely calm and strictly still. Movement accelerates venom spread.\n"
    "2. Immobilize the bitten limb (like a broken bone) at or slightly below heart level.\n"
    "3. Remove tight rings, bangles, watches, and shoes before swelling starts.\n"
    "4. *DO NOT cut or suck the wound.*\n"
    "5. *DO NOT apply ice, herbs, or electricity.*\n"
    "6. *DO NOT tie tight tourniquets.* If a tourniquet is already tied, DO NOT remove it in the field.\n"
    "7. Proceed immediately to the nearest hospital with Anti-Snake Venom (ASV) or dial *108 Emergency Ambulance*."
)


# -----------------------------------------------------------------------------
# 1. Meta WhatsApp Webhook Payload Models
# -----------------------------------------------------------------------------
class WhatsAppText(BaseModel):
    body: str = Field(..., description="Message text content")


class WhatsAppLocation(BaseModel):
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    name: Optional[str] = Field(None, description="Location name if provided by user")
    address: Optional[str] = Field(None, description="Location address if provided by user")


class WhatsAppInteractiveButtonReply(BaseModel):
    id: str
    title: str


class WhatsAppInteractive(BaseModel):
    type: str
    button_reply: Optional[WhatsAppInteractiveButtonReply] = None


class WhatsAppInboundMessage(BaseModel):
    id: str = Field(..., description="Unique WhatsApp message ID (e.g. wamid.HBgM...)")
    from_: str = Field(..., alias="from", description="Sender WhatsApp telephone number (e.g. 919876543210)")
    timestamp: str = Field(..., description="Unix timestamp of message")
    type: str = Field(default="text", description="Message type: text, location, interactive, etc.")
    text: Optional[WhatsAppText] = None
    location: Optional[WhatsAppLocation] = None
    interactive: Optional[WhatsAppInteractive] = None

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class WhatsAppMetadata(BaseModel):
    display_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None


class WhatsAppContact(BaseModel):
    profile: Optional[Dict[str, Any]] = None
    wa_id: Optional[str] = None


class WhatsAppValue(BaseModel):
    messaging_product: str = "whatsapp"
    metadata: Optional[WhatsAppMetadata] = None
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppInboundMessage]] = None
    statuses: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(extra="ignore")


class WhatsAppChange(BaseModel):
    field: str
    value: WhatsAppValue

    model_config = ConfigDict(extra="ignore")


class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]

    model_config = ConfigDict(extra="ignore")


class MetaWebhookPayload(BaseModel):
    object: str
    entry: List[WhatsAppEntry]

    model_config = ConfigDict(extra="ignore")


# -----------------------------------------------------------------------------
# 2. Dhwani-Sanjeevani Backend Assistant Models
# -----------------------------------------------------------------------------
class GPSLocationPayload(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_m: Optional[float] = None
    village: Optional[str] = None
    landmark: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class AssistantMessageRequest(BaseModel):
    channel: str = Field(default="WHATSAPP", description="Access channel (IVR, WHATSAPP, FLUTTER)")
    conversation_id: Optional[str] = Field(None, description="Persistent conversation session ID")
    message: str = Field(..., min_length=1, description="User utterance or transcript")
    case_id: Optional[str] = Field(None, description="Active emergency case ID if known")
    location: Optional[GPSLocationPayload] = Field(None, description="GPS coordinates or location context")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional conversational context")


class FacilityItem(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    state_name: str
    district_name: str
    subdistrict_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    asv_stock_status: str = "UNKNOWN"
    asv_quantity_vials: Optional[int] = None
    asv_verification_source: str = "NOT_VERIFIED"
    asv_notes: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class ReferralInfo(BaseModel):
    facility_id: str
    referral_status: str
    timestamp: Optional[str] = None
    notes: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class AssistantMessageResponse(BaseModel):
    conversation_id: str
    intent: str
    intent_confidence: float
    response_text: str
    case_id: Optional[str] = None
    case_status: Optional[str] = None
    next_action: str = "CONTINUE"
    missing_information: List[str] = Field(default_factory=list)
    nearby_facilities: Optional[List[FacilityItem]] = None
    referral: Optional[ReferralInfo] = None
    safety_metadata: Dict[str, Any] = Field(default_factory=dict)
    is_fallback: bool = False

    model_config = ConfigDict(extra="ignore")


# -----------------------------------------------------------------------------
# 3. User Session State Model (Persistence)
# -----------------------------------------------------------------------------
class UserSession(BaseModel):
    whatsapp_id: str
    conversation_id: Optional[str] = None
    case_id: Optional[str] = None
    last_message_id: Optional[str] = None
    last_user_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message_count: int = 0

    model_config = ConfigDict(extra="ignore")
