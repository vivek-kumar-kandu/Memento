from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.facility import (
    FacilityNearbyQuery,
    FacilityNearbyResponse,
    FacilityDetailResponse,
    ASVStatusResponse,
    FacilityListResponse,
)
from app.schemas.common import FacilityTypeEnum, ASVStatusEnum
from app.services.facility_service import facility_service

router = APIRouter(prefix="/facilities", tags=["Facilities & ASV Inventory"])


@router.get(
    "/nearby",
    response_model=FacilityNearbyResponse,
    summary="Search Nearest PHCs/CHCs by GPS Coordinates (GET)",
    description=(
        "Performs fast spatial radius lookup using a Haversine BallTree index across "
        "34,936 validated health facilities. Accepts query parameters for latitude, longitude, "
        "radius_km, and limit. Ideal for direct Flutter/mobile GPS client integration."
    ),
)
async def find_nearby_facilities_get(
    latitude: float = Query(
        ...,
        ge=-90.0,
        le=90.0,
        description="User or incident latitude in decimal degrees (-90 to 90)",
    ),
    longitude: float = Query(
        ...,
        ge=-180.0,
        le=180.0,
        description="User or incident longitude in decimal degrees (-180 to 180)",
    ),
    radius_km: float = Query(
        30.0,
        gt=0.0,
        le=150.0,
        description="Search radius in kilometres (max 150 km)",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum number of facilities to return (1 to 50)",
    ),
    facility_type: Optional[FacilityTypeEnum] = Query(
        None,
        description="Optional filter: 'PHC' or 'CHC'",
    ),
    state_name: Optional[str] = Query(
        None,
        description="Optional filter by state name",
    ),
    district_name: Optional[str] = Query(
        None,
        description="Optional filter by district name",
    ),
    asv_status: Optional[ASVStatusEnum] = Query(
        None,
        description="Optional filter by ASV stock status (AVAILABLE, OUT_OF_STOCK, UNKNOWN)",
    ),
) -> FacilityNearbyResponse:
    import math
    if math.isnan(latitude) or math.isnan(longitude) or math.isnan(radius_km):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Coordinate and radius parameters must be finite numbers, not NaN.",
        )
    if math.isinf(latitude) or math.isinf(longitude) or math.isinf(radius_km):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Coordinate and radius parameters must be finite numbers, not Infinity.",
        )
    try:
        query = FacilityNearbyQuery(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit,
            facility_type=facility_type,
            state_name=state_name,
            district_name=district_name,
            asv_status=asv_status,
        )
        return facility_service.search_nearby(query)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    "/nearby",
    response_model=FacilityNearbyResponse,
    summary="Search Nearest PHCs/CHCs by Coordinates",
    description=(
        "Performs fast spatial radius lookup using a Haversine BallTree index across "
        "34,936 validated health facilities. Excludes quarantined coordinates. "
        "Returns exact distances in kilometres. Does not fabricate road travel times."
    ),
)
async def find_nearby_facilities(
    query: FacilityNearbyQuery,
) -> FacilityNearbyResponse:
    try:
        response = facility_service.search_nearby(query)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.get(
    "/{facility_id}/asv-status",
    response_model=ASVStatusResponse,
    summary="Get Facility Anti-Snake Venom (ASV) Stock Status",
    description=(
        "Retrieves the recorded ASV inventory status for a specific facility. "
        "All baseline facilities report UNKNOWN by default until verified through "
        "authorized operational reporting. Never assume stock is available without live confirmation."
    ),
)
async def get_facility_asv_status(
    facility_id: str,
    db: AsyncSession = Depends(get_db),
) -> ASVStatusResponse:
    asv_status = await facility_service.get_asv_status(facility_id, db)
    if not asv_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with ID '{facility_id}' not found.",
        )
    return asv_status


@router.get(
    "/{facility_id}",
    response_model=FacilityDetailResponse,
    summary="Get Complete Facility Profile by ID",
    description="Retrieves administrative, coordinate, and ASV inventory information for a single health facility.",
)
async def get_facility_by_id(
    facility_id: str,
    db: AsyncSession = Depends(get_db),
) -> FacilityDetailResponse:
    facility = await facility_service.get_facility_by_id(facility_id, db)
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with ID '{facility_id}' not found.",
        )
    return facility


@router.get(
    "",
    response_model=FacilityListResponse,
    summary="Browse and Filter Facilities Directory",
    description="Browse all facilities with filtering by PHC/CHC type, state name, and district name.",
)
async def list_facilities(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    facility_type: Optional[FacilityTypeEnum] = Query(None, description="Filter: PHC or CHC"),
    state_name: Optional[str] = Query(None, description="Case-insensitive state substring filter"),
    district_name: Optional[str] = Query(None, description="Case-insensitive district substring filter"),
    db: AsyncSession = Depends(get_db),
) -> FacilityListResponse:
    return await facility_service.list_facilities(
        session=db,
        skip=skip,
        limit=limit,
        facility_type=facility_type.value if facility_type else None,
        state_name=state_name,
        district_name=district_name,
    )
