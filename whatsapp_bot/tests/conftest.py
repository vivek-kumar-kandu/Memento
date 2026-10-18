import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure whatsapp_bot directory is in sys.path
_WA_DIR = Path(__file__).resolve().parent.parent
if str(_WA_DIR) not in sys.path:
    sys.path.insert(0, str(_WA_DIR))

from main import app
from session_manager import SessionManager, session_manager
from models import AssistantMessageResponse, FacilityItem, ReferralInfo


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_session_manager(tmp_path):
    """Provides an isolated SessionManager using a temporary file."""
    temp_file = tmp_path / "test_whatsapp_sessions.json"
    mgr = SessionManager(storage_path=str(temp_file))
    mgr.clear_all()
    return mgr


@pytest.fixture(autouse=True)
def clean_global_session():
    """Ensure global session_manager starts clean for each test."""
    session_manager.clear_all()
    yield
    session_manager.clear_all()


class MockBackendClient:
    """Mock backend client simulating Dhwani-Sanjeevani FastAPI backend responses."""

    def __init__(self):
        self.call_history = []
        self.should_fail = False
        self.should_timeout = False

    async def send_message(
        self,
        message: str,
        conversation_id=None,
        case_id=None,
        location=None,
        context=None,
        client=None,
    ) -> AssistantMessageResponse:
        self.call_history.append({
            "message": message,
            "conversation_id": conversation_id,
            "case_id": case_id,
            "location": location,
            "context": context,
        })

        if self.should_fail:
            from models import EMERGENCY_FALLBACK_TEXT
            return AssistantMessageResponse(
                conversation_id=conversation_id or "fallback-session-wa",
                intent="emergency_fallback",
                intent_confidence=1.0,
                response_text=EMERGENCY_FALLBACK_TEXT,
                case_id=case_id,
                case_status="ESCALATED",
                next_action="ESCALATE_HUMAN",
                missing_information=[],
                nearby_facilities=None,
                referral=None,
                safety_metadata={"tourniquet_warning": "Do NOT remove any tourniquet in the field."},
                is_fallback=True,
            )

        cid = conversation_id or "test-conv-uuid-1234"

        # Turn 1: Emergency report without location
        if "saanp" in message.lower() or "kaat" in message.lower() or "snake" in message.lower():
            return AssistantMessageResponse(
                conversation_id=cid,
                intent="emergency_report",
                intent_confidence=0.92,
                response_text="Emergency case recorded (Case ID: DS-2026-TEST01). Keep patient completely still. Do not cut or suck wound. If tourniquet is applied, DO NOT remove it. Send your village or location pin.",
                case_id="DS-2026-TEST01",
                case_status="NEW",
                next_action="COLLECT_LOCATION",
                missing_information=["location"],
                nearby_facilities=None,
                referral=None,
                safety_metadata={
                    "asv_verification_status": "UNKNOWN/NOT_VERIFIED",
                    "asv_safety_notice": "Anti-Snake Venom (ASV) availability is NOT GUARANTEED without live confirmation.",
                    "tourniquet_warning": "Do NOT remove any tourniquet in the field if already applied.",
                },
                is_fallback=False,
            )

        # Turn 2: Location response
        elif "lucknow" in message.lower() or "bakshi" in message.lower() or "location pin" in message.lower() or location is not None:
            return AssistantMessageResponse(
                conversation_id=cid,
                intent="location_response",
                intent_confidence=0.88,
                response_text="Location received. Nearest facility: CHC Mohanlalganj (4.2 km). Referral initiated with status PENDING. Arrange immediate 108 ambulance transport.",
                case_id=case_id or "DS-2026-TEST01",
                case_status="REFERRAL_MADE",
                next_action="DISPATCH_OR_TRANSPORT",
                missing_information=[],
                nearby_facilities=[
                    FacilityItem(
                        facility_id="HCF-014923",
                        facility_name="CHC Mohanlalganj",
                        facility_type="CHC",
                        state_name="Uttar Pradesh",
                        district_name="Lucknow",
                        subdistrict_name="Mohanlalganj",
                        distance_km=4.2,
                        asv_stock_status="UNKNOWN",
                        asv_quantity_vials=None,
                        asv_verification_source="NOT_VERIFIED",
                        asv_notes="Baseline record. Real stock unconfirmed.",
                    )
                ],
                referral=ReferralInfo(
                    facility_id="HCF-014923",
                    referral_status="PENDING",
                    timestamp="2026-10-18T05:00:00Z",
                    notes="Auto-referred to nearest CHC.",
                ),
                safety_metadata={
                    "asv_verification_status": "UNKNOWN/NOT_VERIFIED",
                    "asv_safety_notice": "Anti-Snake Venom availability is UNVERIFIED.",
                    "tourniquet_warning": "Do NOT remove tourniquet in field.",
                },
                is_fallback=False,
            )

        # Turn 3: Follow-up question
        else:
            return AssistantMessageResponse(
                conversation_id=cid,
                intent="first_aid_query",
                intent_confidence=0.85,
                response_text="Keep bitten limb immobilized below heart level. Keep patient lying down. Ambulance 108 is recommended. Do not allow patient to walk.",
                case_id=case_id or "DS-2026-TEST01",
                case_status="REFERRAL_MADE",
                next_action="CONTINUE",
                missing_information=[],
                nearby_facilities=None,
                referral=None,
                safety_metadata={"tourniquet_warning": "Do NOT remove tourniquet in field."},
                is_fallback=False,
            )


@pytest.fixture
def mock_backend():
    return MockBackendClient()
