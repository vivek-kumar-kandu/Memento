import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.case import EmergencyCase
from app.schemas.common import CaseStatus, ReferralStatus
from app.schemas.case import (
    EmergencyCaseCreate,
    EmergencyCaseUpdate,
    EmergencyCaseResponse,
    ReferralInfo,
    ReferralCreateRequest,
    ReferralAcknowledgeRequest,
)


class CaseService:
    @staticmethod
    def _generate_case_id() -> str:
        """Generate a stable, human-readable case identifier."""
        year = datetime.now(timezone.utc).year
        suffix = uuid.uuid4().hex[:6].upper()
        return f"DS-{year}-{suffix}"

    @staticmethod
    def get_first_aid_advisory(tourniquet_applied: Optional[bool] = None) -> Dict[str, Any]:
        """Clinician-reviewed first aid advisory adhering to national/WHO snakebite protocols."""
        tourniquet_warning = (
            "CRITICAL MEDICAL ADVISORY: If a tourniquet or tight ligature is already tied, "
            "DO NOT REMOVE IT IN THE FIELD. Sudden release can cause rapid systemic distribution "
            "of venom and fatal hemodynamic collapse. Trained clinicians must release it gradually "
            "in the hospital with antivenom and resuscitation ready."
            if tourniquet_applied
            else None
        )

        return {
            "tourniquet_warning": tourniquet_warning,
            "do_instructions": [
                "Keep patient completely calm and strictly immobile; movement accelerates venom distribution.",
                "Immobilize the bitten extremity (splint or sling) at or slightly below heart level.",
                "Remove tight items (rings, bangles, watches, tight clothing) before swelling occurs.",
                "Call 108 emergency ambulance immediately and expedite hospital transport.",
            ],
            "dont_instructions": [
                "DO NOT cut, slash, or incise the wound.",
                "DO NOT attempt to suck venom by mouth or mechanical pump.",
                "DO NOT apply ice, electricity, herbs, potassium permanganate, or chemicals.",
                "DO NOT attempt to catch or kill the snake; do not delay transport.",
            ],
            "safety_note": (
                "Anti-Snake Venom (ASV) is the only definitive treatment for envenomation. "
                "Never delay hospital referral to look for local remedies or wait for symptoms to worsen."
            ),
        }

    def format_case_response(self, case: EmergencyCase) -> EmergencyCaseResponse:
        """Format an ORM EmergencyCase into an EmergencyCaseResponse."""
        referral_info = None
        if case.referral_facility_id:
            ref_status = ReferralStatus(case.referral_status) if case.referral_status else ReferralStatus.PENDING
            referral_info = ReferralInfo(
                facility_id=case.referral_facility_id,
                referral_status=ref_status,
                timestamp=case.referral_timestamp,
                notes=case.referral_notes,
                acknowledged_by=case.acknowledged_by,
                acknowledged_at=case.acknowledged_at,
            )

        # Infer tourniquet warning from notes or symptoms if any
        has_tourniquet = False
        if case.referral_notes and "tourniquet" in case.referral_notes.lower():
            has_tourniquet = True
        if case.symptoms:
            for s in case.symptoms:
                if "tourniquet" in s.lower():
                    has_tourniquet = True

        advisory = self.get_first_aid_advisory(tourniquet_applied=has_tourniquet)

        return EmergencyCaseResponse(
            id=case.id,
            channel=case.channel,
            status=CaseStatus(case.status),
            created_at=case.created_at,
            updated_at=case.updated_at,
            reporter_name=case.reporter_name,
            phone_number=case.phone_number,
            location=case.location,
            village=case.village,
            landmark=case.landmark,
            symptoms=case.symptoms,
            referral_facility_id=case.referral_facility_id,
            referral_status=ReferralStatus(case.referral_status) if case.referral_status else None,
            referral_timestamp=case.referral_timestamp,
            referral=referral_info,
            first_aid_advisory=advisory,
        )

    async def create_case(
        self, payload: EmergencyCaseCreate, db: AsyncSession
    ) -> EmergencyCaseResponse:
        """Create a new emergency case with stable ID."""
        case_id = self._generate_case_id()
        initial_status = CaseStatus.TRIAGED.value if payload.symptoms else CaseStatus.NEW.value

        notes = []
        if payload.tourniquet_applied:
            notes.append("Tourniquet applied by bystander prior to call.")

        case = EmergencyCase(
            id=case_id,
            channel=payload.channel.value,
            reporter_name=payload.reporter_name,
            phone_number=payload.phone_number,
            location=payload.location,
            village=payload.village,
            landmark=payload.landmark,
            symptoms=payload.symptoms,
            status=initial_status,
            referral_notes="; ".join(notes) if notes else None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(case)
        await db.commit()
        await db.refresh(case)
        logger.info(f"Created emergency case {case.id} via channel {case.channel}")
        return self.format_case_response(case)

    async def get_case(self, case_id: str, db: AsyncSession) -> Optional[EmergencyCaseResponse]:
        """Retrieve emergency case by ID."""
        stmt = select(EmergencyCase).where(EmergencyCase.id == case_id)
        result = await db.execute(stmt)
        case = result.scalar_one_or_none()
        if not case:
            return None
        return self.format_case_response(case)

    async def update_case(
        self, case_id: str, payload: EmergencyCaseUpdate, db: AsyncSession
    ) -> Optional[EmergencyCaseResponse]:
        """Update mutable fields on an emergency case."""
        stmt = select(EmergencyCase).where(EmergencyCase.id == case_id)
        result = await db.execute(stmt)
        case = result.scalar_one_or_none()
        if not case:
            return None

        if payload.reporter_name is not None:
            case.reporter_name = payload.reporter_name
        if payload.phone_number is not None:
            case.phone_number = payload.phone_number
        if payload.location is not None:
            case.location = payload.location
        if payload.village is not None:
            case.village = payload.village
        if payload.landmark is not None:
            case.landmark = payload.landmark
        if payload.symptoms is not None:
            case.symptoms = payload.symptoms
        if payload.status is not None:
            case.status = payload.status.value
        if payload.referral_facility_id is not None:
            case.referral_facility_id = payload.referral_facility_id
        if payload.referral_status is not None:
            case.referral_status = payload.referral_status.value
        if payload.tourniquet_applied is not None and payload.tourniquet_applied:
            current_notes = case.referral_notes or ""
            if "Tourniquet applied" not in current_notes:
                case.referral_notes = (current_notes + "; Tourniquet applied.").strip("; ")

        case.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(case)
        logger.info(f"Updated emergency case {case.id}")
        return self.format_case_response(case)

    async def add_referral(
        self, case_id: str, info: ReferralCreateRequest, db: AsyncSession
    ) -> Optional[EmergencyCaseResponse]:
        """Create or update referral record for a case."""
        stmt = select(EmergencyCase).where(EmergencyCase.id == case_id)
        result = await db.execute(stmt)
        case = result.scalar_one_or_none()
        if not case:
            return None

        case.referral_facility_id = info.facility_id
        case.referral_status = info.referral_status.value
        case.referral_timestamp = info.timestamp or datetime.now(timezone.utc)
        if info.notes:
            case.referral_notes = info.notes
        case.status = CaseStatus.REFERRAL_MADE.value
        case.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(case)
        logger.info(f"Referral created for case {case.id} to facility {info.facility_id}")
        return self.format_case_response(case)

    async def acknowledge_referral(
        self, case_id: str, ack: ReferralAcknowledgeRequest, db: AsyncSession
    ) -> Optional[EmergencyCaseResponse]:
        """Acknowledge receipt of a referral by an authorized facility staff member."""
        stmt = select(EmergencyCase).where(EmergencyCase.id == case_id)
        result = await db.execute(stmt)
        case = result.scalar_one_or_none()
        if not case:
            return None

        if not case.referral_facility_id:
            raise ValueError(f"Case {case_id} does not have an active referral to acknowledge.")

        case.referral_status = ReferralStatus.ACKNOWLEDGED.value
        case.acknowledged_by = ack.acknowledged_by
        case.acknowledged_at = datetime.now(timezone.utc)
        if ack.notes:
            existing = case.referral_notes or ""
            case.referral_notes = f"{existing}; Ack note: {ack.notes}".strip("; ")
        case.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(case)
        logger.info(f"Referral for case {case.id} acknowledged by {ack.acknowledged_by}")
        return self.format_case_response(case)


case_service = CaseService()
