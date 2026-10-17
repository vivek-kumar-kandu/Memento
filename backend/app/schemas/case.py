from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.schemas.common import Channel, CaseStatus, ReferralStatus


class ReferralInfo(BaseModel):
    facility_id: str = Field(..., description="Healthcare facility ID to which the case is referred")
    referral_status: ReferralStatus = Field(default=ReferralStatus.PENDING, description="Referral lifecycle status")
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReferralCreateRequest(BaseModel):
    facility_id: str = Field(..., description="Healthcare facility ID to which the case is referred")
    referral_status: ReferralStatus = Field(default=ReferralStatus.PENDING, description="Referral lifecycle status")
    notes: Optional[str] = Field(None, max_length=500)
    timestamp: Optional[datetime] = None


class ReferralAcknowledgeRequest(BaseModel):
    acknowledged_by: str = Field(..., min_length=1, max_length=100, description="Staff member or system acknowledging receipt")
    notes: Optional[str] = Field(None, max_length=500, description="Optional triage or admission notes")


class EmergencyCaseCreate(BaseModel):
    channel: Channel = Field(..., description="Origin channel of the report (IVR, WHATSAPP, FLUTTER)")
    reporter_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    location: Optional[Dict[str, Any]] = Field(None, description="Structured location coordinates (latitude, longitude) or context")
    village: Optional[str] = Field(None, max_length=100)
    landmark: Optional[str] = Field(None, max_length=200)
    symptoms: Optional[List[str]] = Field(None, description="List of reported symptoms (e.g. swelling, severe_pain, drooping_eyelids)")
    tourniquet_applied: Optional[bool] = Field(None, description="Whether a tourniquet or tight band has been applied")

    @field_validator("symptoms")
    @classmethod
    def validate_symptoms(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        cleaned = []
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Symptom strings must be non-empty")
            cleaned.append(item.strip())
        return cleaned


class EmergencyCaseUpdate(BaseModel):
    reporter_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    location: Optional[Dict[str, Any]] = None
    village: Optional[str] = Field(None, max_length=100)
    landmark: Optional[str] = Field(None, max_length=200)
    symptoms: Optional[List[str]] = None
    status: Optional[CaseStatus] = None
    referral_facility_id: Optional[str] = Field(None, max_length=32)
    referral_status: Optional[ReferralStatus] = None
    tourniquet_applied: Optional[bool] = None

    @field_validator("symptoms")
    @classmethod
    def validate_symptoms(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        cleaned = []
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Symptom strings must be non-empty")
            cleaned.append(item.strip())
        return cleaned


class EmergencyCaseResponse(BaseModel):
    id: str
    channel: Channel
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    reporter_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    village: Optional[str] = None
    landmark: Optional[str] = None
    symptoms: Optional[List[str]] = None
    referral_facility_id: Optional[str] = None
    referral_status: Optional[ReferralStatus] = None
    referral_timestamp: Optional[datetime] = None
    referral: Optional[ReferralInfo] = None
    first_aid_advisory: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
