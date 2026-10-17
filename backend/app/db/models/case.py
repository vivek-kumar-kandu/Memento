import enum
from datetime import datetime
from typing import Optional, List, Dict

from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

class CaseStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REFERRAL_MADE = "REFERRAL_MADE"

class Channel(str, enum.Enum):
    IVR = "IVR"
    WHATSAPP = "WHATSAPP"
    FLUTTER = "FLUTTER"

class EmergencyCase(Base, TimestampMixin):
    __tablename__ = "emergency_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    reporter_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    location: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    village: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    landmark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    symptoms: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=CaseStatus.NEW.value, nullable=False)
    referral_facility_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    referral_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    referral_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
