import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_nearby_facilities_multiple_results(client: AsyncClient):
    """Test searching around Lucknow (26.8467, 80.9462) with 25 km radius."""
    payload = {
        "latitude": 26.8467,
        "longitude": 80.9462,
        "radius_km": 25.0,
        "limit": 10,
    }
    response = await client.post("/api/v1/facilities/nearby", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["total_found"] > 0
    facilities = data["facilities"]
    assert len(facilities) <= 10

    # Verify distances are monotonically ascending
    distances = [f["distance_km"] for f in facilities]
    assert distances == sorted(distances)

    # Verify each facility fields and safety contract
    for f in facilities:
        assert f["distance_km"] <= 25.0
        assert f["facility_type"] in ["PHC", "CHC"]
        assert f["asv_stock_status"] == "UNKNOWN"
        assert f["asv_quantity_vials"] is None
        assert f["asv_verification_source"] == "NOT_VERIFIED"
        assert f["asv_data_mode"] == "REAL"
        assert f["latitude"] is not None
        assert f["longitude"] is not None


@pytest.mark.asyncio
async def test_nearby_facilities_missing_coordinates(client: AsyncClient):
    """Test validation failure when latitude and longitude are omitted."""
    # Omit both coordinates
    response = await client.post("/api/v1/facilities/nearby", json={"radius_km": 30.0})
    assert response.status_code == 422

    # Omit longitude
    response = await client.post("/api/v1/facilities/nearby", json={"latitude": 26.8467})
    assert response.status_code == 422

    # Omit latitude
    response = await client.post("/api/v1/facilities/nearby", json={"longitude": 80.9462})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_nearby_facilities_invalid_coordinates(client: AsyncClient):
    """Test validation failure when coordinates exceed mathematical bounds."""
    # Latitude > 90
    response = await client.post(
        "/api/v1/facilities/nearby",
        json={"latitude": 95.0, "longitude": 80.0},
    )
    assert response.status_code == 422

    # Latitude < -90
    response = await client.post(
        "/api/v1/facilities/nearby",
        json={"latitude": -95.0, "longitude": 80.0},
    )
    assert response.status_code == 422

    # Longitude > 180
    response = await client.post(
        "/api/v1/facilities/nearby",
        json={"latitude": 25.0, "longitude": 185.0},
    )
    assert response.status_code == 422

    # Longitude < -180
    response = await client.post(
        "/api/v1/facilities/nearby",
        json={"latitude": 25.0, "longitude": -190.0},
    )
    assert response.status_code == 422

    # String non-numeric
    response = await client.post(
        "/api/v1/facilities/nearby",
        json={"latitude": "twenty-five", "longitude": "eighty"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_nearby_facilities_no_results(client: AsyncClient):
    """Test query in open ocean (Null Island) with small radius returns 0 results."""
    payload = {
        "latitude": 0.0,
        "longitude": 0.0,
        "radius_km": 10.0,
    }
    response = await client.post("/api/v1/facilities/nearby", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] == 0
    assert data["facilities"] == []


@pytest.mark.asyncio
async def test_nearby_facilities_filter_by_type(client: AsyncClient):
    """Test filtering strictly by CHC facility type."""
    payload = {
        "latitude": 26.8467,
        "longitude": 80.9462,
        "radius_km": 30.0,
        "facility_type": "CHC",
        "limit": 5,
    }
    response = await client.post("/api/v1/facilities/nearby", json=payload)
    assert response.status_code == 200
    data = response.json()
    for f in data["facilities"]:
        assert f["facility_type"] == "CHC"


@pytest.mark.asyncio
async def test_get_facility_by_id_success(client: AsyncClient):
    """Test retrieving facility HCF-000001 (CHC Nancowry)."""
    response = await client.get("/api/v1/facilities/HCF-000001")
    assert response.status_code == 200
    data = response.json()
    assert data["facility_id"] == "HCF-000001"
    assert data["facility_name"] == "CHC Nancowry"
    assert data["facility_type"] == "CHC"
    assert data["coordinate_status"] == "OK_BROAD_BOUNDS"
    assert data["asv_stock_status"] == "UNKNOWN"
    assert data["asv_quantity_vials"] is None
    assert data["asv_verification_source"] == "NOT_VERIFIED"


@pytest.mark.asyncio
async def test_get_facility_by_id_not_found(client: AsyncClient):
    """Test 404 for non-existent facility ID."""
    response = await client.get("/api/v1/facilities/HCF-999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_quarantined_facility_handling(client: AsyncClient):
    """Test that quarantined facility HCF-003284 exists in DB with quarantine flag,

    and has null coordinates so it never contaminates spatial results.
    """
    response = await client.get("/api/v1/facilities/HCF-003284")
    assert response.status_code == 200
    data = response.json()
    assert data["facility_id"] == "HCF-003284"
    assert data["coordinate_status"] == "OUTSIDE_BROAD_INDIA_BOUNDS"
    assert data["latitude"] is None
    assert data["longitude"] is None


@pytest.mark.asyncio
async def test_get_facility_asv_status(client: AsyncClient):
    """Test dedicated ASV status endpoint and safety disclaimer."""
    response = await client.get("/api/v1/facilities/HCF-000001/asv-status")
    assert response.status_code == 200
    data = response.json()
    assert data["facility_id"] == "HCF-000001"
    assert data["asv_stock_status"] == "UNKNOWN"
    assert data["asv_quantity_vials"] is None
    assert data["verification_source"] == "NOT_VERIFIED"
    assert "safety_disclaimer" in data
    assert "NOT GUARANTEED" in data["safety_disclaimer"]


@pytest.mark.asyncio
async def test_list_facilities_with_state_filter(client: AsyncClient):
    """Test directory list with state filter."""
    response = await client.get("/api/v1/facilities?state_name=Goa&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["facilities"]) <= 10
    for f in data["facilities"]:
        assert "goa" in f["state_name"].lower()


@pytest.mark.asyncio
async def test_nearby_facilities_get_endpoint_success(client: AsyncClient):
    """Test Flutter-style GET /api/v1/facilities/nearby with query parameters."""
    response = await client.get(
        "/api/v1/facilities/nearby",
        params={
            "latitude": 26.8467,
            "longitude": 80.9462,
            "radius_km": 25.0,
            "limit": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] > 0
    assert len(data["facilities"]) <= 5
    assert data["query_latitude"] == 26.8467
    assert data["query_longitude"] == 80.9462

    # Verify distance ordering and facility fields
    distances = [f["distance_km"] for f in data["facilities"]]
    assert distances == sorted(distances)
    for f in data["facilities"]:
        assert f["distance_km"] <= 25.0
        assert f["asv_stock_status"] == "UNKNOWN"
        assert f["asv_quantity_vials"] is None
        assert f["asv_verification_source"] == "NOT_VERIFIED"
        assert "facility_address" in f


@pytest.mark.asyncio
async def test_nearby_facilities_get_missing_coords(client: AsyncClient):
    """Test 422 validation error when required GET query parameters are missing."""
    # Missing longitude
    res1 = await client.get("/api/v1/facilities/nearby", params={"latitude": 26.8467})
    assert res1.status_code == 422

    # Missing latitude
    res2 = await client.get("/api/v1/facilities/nearby", params={"longitude": 80.9462})
    assert res2.status_code == 422


@pytest.mark.asyncio
async def test_nearby_facilities_get_out_of_bounds_coords(client: AsyncClient):
    """Test 422 validation when coordinates violate geographic bounds."""
    # Latitude > 90
    res1 = await client.get(
        "/api/v1/facilities/nearby",
        params={"latitude": 105.0, "longitude": 80.0},
    )
    assert res1.status_code == 422

    # Longitude > 180
    res2 = await client.get(
        "/api/v1/facilities/nearby",
        params={"latitude": 25.0, "longitude": 195.0},
    )
    assert res2.status_code == 422


@pytest.mark.asyncio
async def test_nearby_facilities_nan_and_inf_rejected(client: AsyncClient):
    """Test that NaN and Infinity coordinates are rejected with 422 for both GET and POST."""
    # POST with NaN
    res_post_nan = await client.post(
        "/api/v1/facilities/nearby",
        json={"latitude": "NaN", "longitude": 80.9462},
    )
    assert res_post_nan.status_code == 422

    # POST with Infinity
    res_post_inf = await client.post(
        "/api/v1/facilities/nearby",
        json={"latitude": "Infinity", "longitude": 80.9462},
    )
    assert res_post_inf.status_code == 422

    # GET with NaN
    res_get_nan = await client.get(
        "/api/v1/facilities/nearby",
        params={"latitude": "nan", "longitude": 80.9462},
    )
    assert res_get_nan.status_code == 422


@pytest.mark.asyncio
async def test_nearby_facilities_get_empty_results(client: AsyncClient):
    """Test query returning valid empty result without inventing facilities."""
    res = await client.get(
        "/api/v1/facilities/nearby",
        params={"latitude": 0.0, "longitude": 0.0, "radius_km": 10.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_found"] == 0
    assert data["facilities"] == []
    assert "safety_disclaimer" in data
