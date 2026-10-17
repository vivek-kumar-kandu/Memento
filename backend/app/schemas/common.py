import enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Channel(str, enum.Enum):
    IVR = "IVR"
    WHATSAPP = "WHATSAPP"
    FLUTTER = "FLUTTER"


class CaseStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    TRIAGED = "TRIAGED"
    REFERRAL_MADE = "REFERRAL_MADE"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class ReferralStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class FacilityTypeEnum(str, enum.Enum):
    PHC = "PHC"
    CHC = "CHC"


class ASVStatusEnum(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    UNKNOWN = "UNKNOWN"


class InventoryDataModeEnum(str, enum.Enum):
    REAL = "REAL"
    SIMULATED = "SIMULATED"


class VerificationSourceEnum(str, enum.Enum):
    NOT_VERIFIED = "NOT_VERIFIED"
    TELEPHONE_CALL = "TELEPHONE_CALL"
    FACILITY_PORTAL = "FACILITY_PORTAL"
    STATE_DASHBOARD = "STATE_DASHBOARD"
    DISTRICT_OFFICER = "DISTRICT_OFFICER"


class GeoPoint(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90.0 and 90.0")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180.0 and 180.0")
        return v
