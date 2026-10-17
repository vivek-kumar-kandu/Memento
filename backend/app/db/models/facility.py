import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class FacilityType(str, enum.Enum):
    PHC = "PHC"
    CHC = "CHC"


class CoordinateStatus(str, enum.Enum):
    OK_BROAD_BOUNDS = "OK_BROAD_BOUNDS"
    OUTSIDE_BROAD_INDIA_BOUNDS = "OUTSIDE_BROAD_INDIA_BOUNDS"
    MISSING_OR_NONNUMERIC = "MISSING_OR_NONNUMERIC"


class ASVStockStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    UNKNOWN = "UNKNOWN"


class InventoryDataMode(str, enum.Enum):
    REAL = "REAL"
    SIMULATED = "SIMULATED"


class VerificationSource(str, enum.Enum):
    NOT_VERIFIED = "NOT_VERIFIED"
    TELEPHONE_CALL = "TELEPHONE_CALL"
    FACILITY_PORTAL = "FACILITY_PORTAL"
    STATE_DASHBOARD = "STATE_DASHBOARD"
    DISTRICT_OFFICER = "DISTRICT_OFFICER"


class HealthcareFacility(Base, TimestampMixin):
    __tablename__ = "healthcare_facilities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # e.g. HCF-000001
    source_row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    facility_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    facility_type: Mapped[str] = mapped_column(String(16), index=True, nullable=False)  # PHC / CHC
    state_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    subdistrict_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    facility_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Coordinates: nullable if quarantined / missing
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    coordinate_status: Mapped[str] = mapped_column(
        String(32),
        default=CoordinateStatus.OK_BROAD_BOUNDS.value,
        nullable=False,
    )
    coordinate_validation_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Metadata from national directory
    source_active_flag: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    location_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # Rural / Urban
    source_type_of_facility: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    possible_duplicate_name_in_district: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    # Relationship to ASV Inventory (One-to-One)
    asv_inventory: Mapped[Optional["ASVInventory"]] = relationship(
        "ASVInventory",
        back_populates="facility",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_facility_state_district", "state_name", "district_name"),
        Index("ix_facility_type_status", "facility_type", "coordinate_status"),
    )


class ASVInventory(Base, TimestampMixin):
    __tablename__ = "asv_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    facility_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("healthcare_facilities.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Stock status: AVAILABLE, OUT_OF_STOCK, UNKNOWN (Defaults to UNKNOWN)
    stock_status: Mapped[str] = mapped_column(
        String(24),
        default=ASVStockStatus.UNKNOWN.value,
        nullable=False,
    )
    # Quantity vials: nullable when unknown
    quantity_vials: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)

    # Data Mode: REAL or SIMULATED
    data_mode: Mapped[str] = mapped_column(
        String(16),
        default=InventoryDataMode.REAL.value,
        nullable=False,
    )

    # Verification source
    verification_source: Mapped[str] = mapped_column(
        String(32),
        default=VerificationSource.NOT_VERIFIED.value,
        nullable=False,
    )

    last_inventory_update: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verification_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationship
    facility: Mapped["HealthcareFacility"] = relationship(
        "HealthcareFacility",
        back_populates="asv_inventory",
        lazy="joined",
    )
