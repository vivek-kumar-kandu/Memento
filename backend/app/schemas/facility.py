from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.common import (
    FacilityTypeEnum,
    ASVStatusEnum,
    InventoryDataModeEnum,
    VerificationSourceEnum,
)


class FacilityNearbyQuery(BaseModel):
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="User or incident latitude in decimal degrees",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="User or incident longitude in decimal degrees",
    )
    radius_km: float = Field(
        default=30.0,
        gt=0.0,
        le=150.0,
        description="Search radius in kilometres (max 150 km)",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of facilities to return",
    )
    facility_type: Optional[FacilityTypeEnum] = Field(
        default=None,
        description="Optional filter: 'PHC' or 'CHC'",
    )
    state_name: Optional[str] = Field(
        default=None,
        description="Optional filter by state name",
    )
    district_name: Optional[str] = Field(
        default=None,
        description="Optional filter by district name",
    )
    asv_status: Optional[ASVStatusEnum] = Field(
        default=None,
        description="Optional filter by ASV stock status (AVAILABLE, OUT_OF_STOCK, UNKNOWN)",
    )

    @field_validator("latitude", "longitude", "radius_km", mode="after")
    @classmethod
    def validate_finite_coords(cls, v: float) -> float:
        import math
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Coordinate and radius values must be finite numbers, not NaN or Infinity")
        return v


class FacilityNearbyItem(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    state_name: str
    district_name: str
    subdistrict_name: Optional[str] = None
    facility_address: Optional[str] = None
    latitude: float
    longitude: float
    distance_km: float = Field(..., description="Great-circle distance in kilometres")
    asv_stock_status: str
    asv_quantity_vials: Optional[int] = None
    asv_data_mode: str
    asv_verification_source: str
    asv_last_verified_at: Optional[datetime] = None
    asv_notes: Optional[str] = None


class FacilityNearbyResponse(BaseModel):
    query_latitude: float
    query_longitude: float
    search_radius_km: float
    total_found: int
    facilities: List[FacilityNearbyItem]
    safety_disclaimer: str = (
        "ASV availability is unverified in baseline facility directories. "
        "Always confirm directly or through 108 emergency ambulance dispatch."
    )


class ASVStatusResponse(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    state_name: str
    district_name: str
    subdistrict_name: Optional[str] = None
    asv_stock_status: str
    asv_quantity_vials: Optional[int] = None
    data_mode: str
    verification_source: str
    last_inventory_update: Optional[datetime] = None
    last_verification_timestamp: Optional[datetime] = None
    safety_disclaimer: str = (
        "Anti-Snake Venom (ASV) availability is NOT GUARANTEED unless confirmed by "
        "live operational update. Do not delay transport while attempting to verify stock."
    )


class FacilityDetailResponse(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    state_name: str
    district_name: str
    subdistrict_name: Optional[str] = None
    facility_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coordinate_status: str
    coordinate_validation_note: Optional[str] = None
    location_type: Optional[str] = None
    asv_stock_status: str
    asv_quantity_vials: Optional[int] = None
    asv_data_mode: str
    asv_verification_source: str
    asv_last_verified_at: Optional[datetime] = None


class FacilityListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    facilities: List[FacilityDetailResponse]
