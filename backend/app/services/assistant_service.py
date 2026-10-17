import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.case import EmergencyCase
from app.db.models.conversation import ConversationSession
from app.schemas.common import Channel, CaseStatus, ReferralStatus
from app.schemas.case import EmergencyCaseCreate, ReferralCreateRequest
from app.schemas.assistant import AssistantMessageRequest, AssistantMessageResponse
from app.schemas.facility import FacilityNearbyQuery, FacilityNearbyItem
from app.services.case_service import case_service
from app.services.facility_service import facility_service
from app.services.classifier_service import classifier_service
from app.services.geo_service import geo_index


class AssistantService:
    def __init__(self):
        pass

    @staticmethod
    def extract_coordinates(text: str, location_dict: Optional[Dict[str, Any]] = None) -> Optional[Tuple[float, float]]:
        """Extract valid (lat, lon) from structured dict or text if present."""
        # 1. Structured location dict
        if location_dict:
            try:
                lat = float(location_dict.get("latitude") or location_dict.get("lat"))
                lon = float(location_dict.get("longitude") or location_dict.get("lon") or location_dict.get("lng"))
                if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                    return lat, lon
            except (TypeError, ValueError):
                pass

        # 2. Text regex for decimal coordinates e.g. "26.8467, 80.9462" or "lat: 26.8, lon: 80.9"
        coord_pattern = r"(-?\d{1,2}\.\d{3,8})[,\s]+(-?\d{1,3}\.\d{3,8})"
        match = re.search(coord_pattern, text)
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                if 6.0 <= lat <= 38.0 and 68.0 <= lon <= 98.0:  # Valid Indian bounding box
                    return lat, lon
            except ValueError:
                pass

        return None

    @staticmethod
    def resolve_location_name(text: str, location_dict: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Optional[Tuple[float, float]]]:
        """
        Attempt to resolve a village or subdistrict name from facility directory.
        Returns (resolved_name, (lat, lon)) if verified, else (None, None).
        NEVER fabricates coordinates or distances.
        """
        candidate_name = None
        if location_dict:
            candidate_name = location_dict.get("village") or location_dict.get("landmark") or location_dict.get("name")

        lowered = text.lower()

        # Check in-memory facilities index for real matching subdistrict or district
        if geo_index.is_loaded and geo_index.facilities:
            for fac in geo_index.facilities:
                subdist = (fac.get("subdistrict_name") or "").lower()
                dist = (fac.get("district_name") or "").lower()
                fac_name = (fac.get("facility_name") or "").lower()

                # Check if text contains known subdistrict name (e.g. "bakshi ka talab", "mohanlalganj")
                if subdist and len(subdist) > 3 and subdist in lowered:
                    return fac.get("subdistrict_name"), (fac["latitude"], fac["longitude"])
                if candidate_name and subdist and candidate_name.lower() in subdist:
                    return fac.get("subdistrict_name"), (fac["latitude"], fac["longitude"])

            # Check district level if subdistrict was not matched
            for fac in geo_index.facilities:
                dist = (fac.get("district_name") or "").lower()
                if dist and len(dist) > 3 and dist in lowered:
                    return fac.get("district_name"), (fac["latitude"], fac["longitude"])

        return candidate_name, None

    async def get_or_create_session(
        self, session_id: Optional[str], channel: Channel, db: AsyncSession
    ) -> ConversationSession:
        """Retrieve existing conversation session or initialize a new one."""
        if session_id:
            stmt = select(ConversationSession).where(ConversationSession.id == session_id)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                return existing

        new_session = ConversationSession(
            id=session_id or str(uuid.uuid4()),
            channel=channel.value,
            state="ACTIVE",
            context_data={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return new_session

    async def handle_message(
        self, payload: AssistantMessageRequest, db: AsyncSession
    ) -> AssistantMessageResponse:
        """
        Shared assistant endpoint for IVR, WhatsApp bot, and Flutter app.
        Processes user/caller utterances, persists conversation state across turns,
        creates/links emergency cases, resolves geolocations, and issues referrals.
        """
        # 1. Conversation State Retrieval
        session = await self.get_or_create_session(payload.conversation_id, payload.channel, db)
        context = session.context_data or {}

        # If request explicitly supplied a case_id, link it
        if payload.case_id:
            session.case_id = payload.case_id

        # 2. Intent Classification with Safety Overrides
        clf_result = classifier_service.predict_intent(payload.message)
        intent = clf_result["intent"]
        confidence = clf_result["confidence"]
        is_emergency = clf_result["is_emergency"]
        is_human = clf_result["is_human_escalation"]

        # Track conversation history in context
        history = context.get("history", [])
        history.append({
            "sender": "user",
            "message": payload.message,
            "intent": intent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        case_obj = None
        if session.case_id:
            stmt = select(EmergencyCase).where(EmergencyCase.id == session.case_id)
            res = await db.execute(stmt)
            case_obj = res.scalar_one_or_none()

        nearby_items: Optional[List[FacilityNearbyItem]] = None
        referral_info = None
        missing_info = []
        next_action = "CONTINUE"
        response_text = ""

        safety_metadata = {
            "asv_verification_status": "UNKNOWN/NOT_VERIFIED",
            "asv_safety_notice": (
                "Anti-Snake Venom (ASV) availability is NOT GUARANTEED without live confirmation. "
                "Do not delay transport to verify stock. Call 108 emergency ambulance immediately."
            ),
            "tourniquet_warning": (
                "Do NOT remove any tourniquet in the field if already applied. "
                "Hospital staff will manage tourniquet removal with antivenom prepared."
            ),
            "emergency_numbers": ["108 (Ambulance)", "112 (National Emergency)"],
        }

        # -------------------------------------------------------------
        # Intent Execution Logic
        # -------------------------------------------------------------

        # A. HUMAN HELP / OPERATOR ESCALATION
        if is_human or intent == "human_help":
            next_action = "ESCALATE_HUMAN"
            response_text = (
                "Connecting you immediately to an emergency 108 medical dispatcher. "
                "Please stay on the line. While waiting, keep the patient strictly still and calm."
            )

        # B. EMERGENCY REPORT / NEW SNAKEBITE INCIDENT
        elif intent == "emergency_report" or (is_emergency and not case_obj):
            if not case_obj:
                # Create new case
                case_create = EmergencyCaseCreate(
                    channel=payload.channel,
                    location=payload.location,
                )
                case_resp = await case_service.create_case(case_create, db)
                session.case_id = case_resp.id

                # Fetch ORM instance to update session
                stmt = select(EmergencyCase).where(EmergencyCase.id == case_resp.id)
                res = await db.execute(stmt)
                case_obj = res.scalar_one_or_none()

            # Check if location is already known
            coords = self.extract_coordinates(payload.message, payload.location)
            resolved_name, name_coords = self.resolve_location_name(payload.message, payload.location)
            effective_coords = coords or name_coords

            if effective_coords:
                lat, lon = effective_coords
                case_obj.location = {"latitude": lat, "longitude": lon}
                if resolved_name:
                    case_obj.village = resolved_name
                await db.commit()

                # Find nearby facilities
                search_q = FacilityNearbyQuery(latitude=lat, longitude=lon, radius_km=30.0, limit=5)
                search_res = facility_service.search_nearby(search_q)
                nearby_items = search_res.facilities

                if nearby_items:
                    nearest = nearby_items[0]
                    # Automatically initiate referral (status: PENDING)
                    ref_req = ReferralCreateRequest(
                        facility_id=nearest.facility_id,
                        referral_status=ReferralStatus.PENDING,
                        notes=f"Auto-referred to nearest facility {nearest.facility_name} ({nearest.distance_km:.1f} km away).",
                    )
                    await case_service.add_referral(case_obj.id, ref_req, db)
                    await db.refresh(case_obj)

                    response_text = (
                        f"Emergency case recorded (Case ID: {case_obj.id}). "
                        f"Nearest healthcare facility: {nearest.facility_name} ({nearest.distance_km:.1f} km away). "
                        f"Referral initiated with status PENDING. Call 108 ambulance immediately. "
                        f"Keep the patient strictly immobilized. If a tourniquet is tied, do NOT untie it."
                    )
                    next_action = "DISPATCH_OR_TRANSPORT"
                else:
                    response_text = (
                        f"Emergency case recorded (Case ID: {case_obj.id}). "
                        "No facilities within 30 km; call 108 emergency dispatch for transport."
                    )
                    next_action = "CALL_108"
            else:
                missing_info.append("location")
                next_action = "COLLECT_LOCATION"
                response_text = (
                    f"Emergency case recorded (Case ID: {case_obj.id}). "
                    "Keep the patient completely calm and strictly still. Do not cut or suck the bite wound. "
                    "If a tourniquet is already tied, DO NOT remove it. "
                    "Please provide your current village, landmark, or GPS coordinates so we can route you to the nearest hospital."
                )

        # C. LOCATION RESPONSE (OR ACTIVE CASE AWAITING LOCATION)
        elif intent == "location_response" or (case_obj and not case_obj.location):
            coords = self.extract_coordinates(payload.message, payload.location)
            resolved_name, name_coords = self.resolve_location_name(payload.message, payload.location)
            effective_coords = coords or name_coords

            if effective_coords and case_obj:
                lat, lon = effective_coords
                case_obj.location = {"latitude": lat, "longitude": lon}
                if resolved_name:
                    case_obj.village = resolved_name
                await db.commit()

                # Search nearby
                search_q = FacilityNearbyQuery(latitude=lat, longitude=lon, radius_km=30.0, limit=5)
                search_res = facility_service.search_nearby(search_q)
                nearby_items = search_res.facilities

                if nearby_items:
                    nearest = nearby_items[0]
                    ref_req = ReferralCreateRequest(
                        facility_id=nearest.facility_id,
                        referral_status=ReferralStatus.PENDING,
                        notes=f"Referred to nearest facility {nearest.facility_name} ({nearest.distance_km:.1f} km away).",
                    )
                    await case_service.add_referral(case_obj.id, ref_req, db)
                    await db.refresh(case_obj)

                    response_text = (
                        f"Location received. Nearest healthcare facility: {nearest.facility_name} "
                        f"({nearest.distance_km:.1f} km away). Referral initiated with status PENDING. "
                        f"Please arrange immediate transport via 108 ambulance. "
                        f"Keep the bitten limb immobilized at heart level."
                    )
                    next_action = "DISPATCH_OR_TRANSPORT"
                else:
                    response_text = (
                        f"Location received at ({lat:.4f}, {lon:.4f}). No PHC/CHC found within 30 km. "
                        f"Contact 108 ambulance dispatch immediately for regional hospital transfer."
                    )
                    next_action = "CALL_108"
            elif case_obj:
                # Unable to resolve free-text village without coordinates
                missing_info.append("location")
                next_action = "COLLECT_LOCATION"
                response_text = (
                    "Could not reliably resolve the location name from our facility index. "
                    "Please provide the nearest major town, block/tehsil name, or GPS coordinates from your phone. "
                    "Do not delay seeking medical care."
                )
            else:
                response_text = (
                    "Location noted, but no active emergency case was found. "
                    "If someone has been bitten by a snake, please confirm immediately."
                )
                next_action = "CONFIRM_EMERGENCY"

        # D. FIRST AID QUERY
        elif intent == "first_aid_query":
            next_action = "PROVIDE_FIRST_AID"
            response_text = (
                "FIRST AID GUIDELINES: 1. Keep the patient completely calm and strictly immobile. "
                "2. Immobilize the bitten limb like a fracture. 3. Remove rings, bangles, and tight clothes. "
                "4. DO NOT cut, suck, or apply ice/chemicals. 5. If a tourniquet is already applied, "
                "DO NOT REMOVE IT in the field — hospital staff must remove it safely with antivenom ready. "
                "6. Call 108 immediately for transport."
            )

        # E. SYMPTOM REPORT
        elif intent == "symptom_report":
            if case_obj:
                symptoms = case_obj.symptoms or []
                symptoms.append(payload.message[:100])
                case_obj.symptoms = list(set(symptoms))
                case_obj.status = CaseStatus.TRIAGED.value
                await db.commit()
                await db.refresh(case_obj)

            next_action = "ASSESS_SYMPTOMS"
            response_text = (
                "Symptoms noted and recorded. Systemic symptoms (difficulty breathing, drooping eyelids, "
                "bleeding) require immediate emergency antivenom intervention. "
                "Do not wait for symptoms to worsen; transfer to the nearest designated healthcare facility."
            )

        # F. REPEAT REQUEST
        elif intent == "repeat_request":
            last_resp = context.get("last_response", "Please contact 108 emergency service immediately.")
            response_text = f"Repeating previous instruction: {last_resp}"
            next_action = context.get("last_action", "CONTINUE")

        # G. UNKNOWN / SAFE FALLBACK
        else:
            response_text = (
                "I am Dhwani-Sanjeevani emergency assistant. If this is a snakebite emergency, "
                "please tell me who was bitten and where you are, or ask for an operator."
            )
            next_action = "CLARIFY"

        # Prepare referral output if case has active referral
        if case_obj and case_obj.referral_facility_id:
            ref_status = ReferralStatus(case_obj.referral_status) if case_obj.referral_status else ReferralStatus.PENDING
            referral_info = {
                "facility_id": case_obj.referral_facility_id,
                "referral_status": ref_status,
                "timestamp": case_obj.referral_timestamp,
                "notes": case_obj.referral_notes,
                "acknowledged_by": case_obj.acknowledged_by,
                "acknowledged_at": case_obj.acknowledged_at,
            }

        # Update session context
        context["last_response"] = response_text
        context["last_action"] = next_action
        session.context_data = context
        session.last_message = payload.message
        session.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return AssistantMessageResponse(
            conversation_id=session.id,
            intent=intent,
            intent_confidence=confidence,
            response_text=response_text,
            case_id=case_obj.id if case_obj else None,
            case_status=case_obj.status if case_obj else None,
            next_action=next_action,
            missing_information=missing_info,
            nearby_facilities=nearby_items,
            referral=referral_info,
            safety_metadata=safety_metadata,
        )


assistant_service = AssistantService()
