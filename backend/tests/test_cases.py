import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_case_minimal(client: AsyncClient):
    """Test emergency case creation with required channel."""
    payload = {
        "channel": "IVR",
        "reporter_name": "Ramesh",
        "phone_number": "+919876543210",
    }
    response = await client.post("/api/v1/cases/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("DS-")
    assert data["channel"] == "IVR"
    assert data["status"] == "NEW"
    assert data["reporter_name"] == "Ramesh"
    assert data["phone_number"] == "+919876543210"
    assert data["first_aid_advisory"] is not None
    assert "safety_note" in data["first_aid_advisory"]


@pytest.mark.asyncio
async def test_create_case_with_symptoms_and_tourniquet(client: AsyncClient):
    """Test emergency case creation with symptoms and tourniquet warning."""
    payload = {
        "channel": "WHATSAPP",
        "reporter_name": "Sita Devi",
        "phone_number": "+919876543211",
        "symptoms": ["swelling", "severe_pain", "drooping_eyelids"],
        "village": "Bakshi Ka Talab",
        "tourniquet_applied": True,
    }
    response = await client.post("/api/v1/cases/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "TRIAGED"
    assert data["symptoms"] == ["swelling", "severe_pain", "drooping_eyelids"]
    assert data["first_aid_advisory"]["tourniquet_warning"] is not None
    assert "DO NOT REMOVE IT IN THE FIELD" in data["first_aid_advisory"]["tourniquet_warning"]


@pytest.mark.asyncio
async def test_get_case_success_and_not_found(client: AsyncClient):
    """Test getting an existing case and 404 for nonexistent."""
    # Create first
    res = await client.post("/api/v1/cases/", json={"channel": "FLUTTER"})
    assert res.status_code == 201
    case_id = res.json()["id"]

    # Get existing
    get_res = await client.get(f"/api/v1/cases/{case_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == case_id

    # Nonexistent
    bad_res = await client.get("/api/v1/cases/DS-9999-NONEXISTENT")
    assert bad_res.status_code == 404


@pytest.mark.asyncio
async def test_update_case(client: AsyncClient):
    """Test updating case fields (village, landmark, symptoms)."""
    res = await client.post("/api/v1/cases/", json={"channel": "IVR"})
    case_id = res.json()["id"]

    patch_payload = {
        "village": "Mohanlalganj",
        "landmark": "Near Primary School",
        "symptoms": ["vomiting", "blurred_vision"],
    }
    patch_res = await client.patch(f"/api/v1/cases/{case_id}", json=patch_payload)
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["village"] == "Mohanlalganj"
    assert data["landmark"] == "Near Primary School"
    assert data["symptoms"] == ["vomiting", "blurred_vision"]

    # 404 on update nonexistent
    bad_patch = await client.patch("/api/v1/cases/DS-NONEXISTENT", json={"village": "Test"})
    assert bad_patch.status_code == 404


@pytest.mark.asyncio
async def test_referral_lifecycle_and_acknowledgement(client: AsyncClient):
    """Test referral creation is separate from referral acknowledgement."""
    # 1. Create case
    res = await client.post("/api/v1/cases/", json={"channel": "WHATSAPP"})
    case_id = res.json()["id"]

    # 2. Check no referral initially
    ref_check = await client.get(f"/api/v1/cases/{case_id}/referral")
    assert ref_check.status_code == 404

    # 3. Create referral
    ref_payload = {
        "facility_id": "HCF-031769",
        "referral_status": "PENDING",
        "notes": "Patient en route via 108 ambulance",
    }
    ref_res = await client.post(f"/api/v1/cases/{case_id}/referral", json=ref_payload)
    assert ref_res.status_code == 200
    case_data = ref_res.json()
    assert case_data["status"] == "REFERRAL_MADE"
    assert case_data["referral"]["facility_id"] == "HCF-031769"
    assert case_data["referral"]["referral_status"] == "PENDING"
    assert case_data["referral"]["acknowledged_by"] is None

    # 4. Get referral
    get_ref = await client.get(f"/api/v1/cases/{case_id}/referral")
    assert get_ref.status_code == 200
    assert get_ref.json()["facility_id"] == "HCF-031769"
    assert get_ref.json()["referral_status"] == "PENDING"

    # 5. Acknowledge referral by hospital staff
    ack_payload = {
        "acknowledged_by": "Dr. Verma, CMO CHC",
        "notes": "Emergency bay prepared, ASV vial ready",
    }
    ack_res = await client.post(f"/api/v1/cases/{case_id}/referral/acknowledge", json=ack_payload)
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["referral"]["referral_status"] == "ACKNOWLEDGED"
    assert ack_data["referral"]["acknowledged_by"] == "Dr. Verma, CMO CHC"
    assert ack_data["referral"]["acknowledged_at"] is not None


@pytest.mark.asyncio
async def test_case_validation_errors(client: AsyncClient):
    """Test validation errors on empty symptoms and invalid channels."""
    # Invalid channel
    bad_channel_res = await client.post("/api/v1/cases/", json={"channel": "TELEGRAM"})
    assert bad_channel_res.status_code == 422

    # Empty symptom string
    bad_symptom_res = await client.post(
        "/api/v1/cases/",
        json={"channel": "IVR", "symptoms": ["   "]},
    )
    assert bad_symptom_res.status_code == 422


@pytest.mark.asyncio
async def test_acknowledge_without_referral_errors(client: AsyncClient):
    """Test that acknowledging a case without an active referral fails safely with 400."""
    res = await client.post("/api/v1/cases/", json={"channel": "IVR"})
    case_id = res.json()["id"]

    ack_res = await client.post(
        f"/api/v1/cases/{case_id}/referral/acknowledge",
        json={"acknowledged_by": "Dr. Singh"},
    )
    assert ack_res.status_code == 400
    assert "does not have an active referral" in ack_res.json()["detail"]

    # Nonexistent case
    ack_res_404 = await client.post(
        "/api/v1/cases/DS-9999-NOTFOUND/referral/acknowledge",
        json={"acknowledged_by": "Dr. Singh"},
    )
    assert ack_res_404.status_code == 404

