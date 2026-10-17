from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.db.session import get_db
from app.schemas.case import (
    EmergencyCaseCreate,
    EmergencyCaseUpdate,
    EmergencyCaseResponse,
    ReferralInfo,
)
from app.services.case_service import case_service

router = APIRouter(prefix="/cases", tags=["Emergency Cases"])

@router.post("/", response_model=EmergencyCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(payload: EmergencyCaseCreate, db: AsyncSession = Depends(get_db)):
    case = await case_service.create_case(payload, db)
    return case

@router.get("/{case_id}", response_model=EmergencyCaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    case = await case_service.get_case(case_id, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case

@router.patch("/{case_id}", response_model=EmergencyCaseResponse)
async def update_case(case_id: str, payload: EmergencyCaseUpdate, db: AsyncSession = Depends(get_db)):
    updated = await case_service.update_case(case_id, payload, db)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return updated

@router.post("/{case_id}/referral", response_model=EmergencyCaseResponse)
async def add_referral(case_id: str, info: ReferralInfo, db: AsyncSession = Depends(get_db)):
    case = await case_service.add_referral(case_id, info, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case
