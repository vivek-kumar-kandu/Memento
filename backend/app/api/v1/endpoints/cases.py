from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.case import (
    EmergencyCaseCreate,
    EmergencyCaseUpdate,
    EmergencyCaseResponse,
    ReferralInfo,
    ReferralCreateRequest,
    ReferralAcknowledgeRequest,
)
from app.services.case_service import case_service

router = APIRouter(prefix="/cases", tags=["Emergency Cases"])


@router.post("/", response_model=EmergencyCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(payload: EmergencyCaseCreate, db: AsyncSession = Depends(get_db)):
    """Create a new emergency case."""
    return await case_service.create_case(payload, db)


@router.get("/{case_id}", response_model=EmergencyCaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve an emergency case by ID."""
    case = await case_service.get_case(case_id, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")
    return case


@router.patch("/{case_id}", response_model=EmergencyCaseResponse)
async def update_case(case_id: str, payload: EmergencyCaseUpdate, db: AsyncSession = Depends(get_db)):
    """Update fields of an emergency case."""
    updated = await case_service.update_case(case_id, payload, db)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")
    return updated


@router.post("/{case_id}/referral", response_model=EmergencyCaseResponse)
async def create_referral(case_id: str, info: ReferralCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create or update a referral to a destination healthcare facility."""
    case = await case_service.add_referral(case_id, info, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")
    return case


@router.get("/{case_id}/referral", response_model=ReferralInfo)
async def get_referral(case_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve referral details for a case."""
    case = await case_service.get_case(case_id, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")
    if not case.referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No referral found for case '{case_id}'")
    return case.referral


@router.post("/{case_id}/referral/acknowledge", response_model=EmergencyCaseResponse)
async def acknowledge_referral(case_id: str, ack: ReferralAcknowledgeRequest, db: AsyncSession = Depends(get_db)):
    """Acknowledge referral receipt by authorized healthcare staff."""
    try:
        case = await case_service.acknowledge_referral(case_id, ack, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")
    return case
