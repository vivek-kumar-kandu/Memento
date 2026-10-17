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
from app.schemas.common import FacilityTypeEnum
from app.services.facility_service import facility_service

router = APIRouter(prefix="/facilities", tags=["Facilities & ASV Inventory"])


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
