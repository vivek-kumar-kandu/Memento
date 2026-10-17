from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from app.schemas.common import Channel

class EmergencyCaseCreate(BaseModel):
    channel: Channel = Field(..., description='Origin channel of the report')
    reporter_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    location: Optional[Dict[str, Any]] = Field(None, description='Free-form location data, e.g., lat/lon or address')
    village: Optional[str] = Field(None, max_length=100)
    landmark: Optional[str] = Field(None, max_length=200)
    symptoms: Optional[List[str]] = Field(None, description='List of reported symptoms')

    @validator('symptoms', each_item=True)
    def non_empty_symptom(cls, v):
        if not v or not v.strip():
            raise ValueError('symptom strings must be non-empty')
        return v

class EmergencyCaseUpdate(BaseModel):
    reporter_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    location: Optional[Dict[str, Any]] = None
    village: Optional[str] = Field(None, max_length=100)
    landmark: Optional[str] = Field(None, max_length=200)
    symptoms: Optional[List[str]] = None
    status: Optional[str] = None

class ReferralInfo(BaseModel):
    facility_id: str = Field(..., description='Facility ID to which the case is referred')
    referral_status: str = Field(..., description='Status of the referral, e.g., SENT, ACKNOWLEDGED')
    timestamp: Optional[datetime] = None

class EmergencyCaseResponse(BaseModel):
    id: str
    channel: Channel
    status: str
    created_at: datetime
    updated_at: datetime
    reporter_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    village: Optional[str] = None
    landmark: Optional[str] = None
    symptoms: Optional[List[str]] = None
    referral: Optional[ReferralInfo] = None

    class Config:
        orm_mode = True
