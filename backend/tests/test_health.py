import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_root_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "connected"
    assert data["facility_index"]["status"] == "ready"
    assert data["facility_index"]["valid_indexed_facilities"] == 34936
    assert data["facility_index"]["quarantined_facilities_excluded"] == 186
    assert data["facility_index"]["total_source_facilities"] == 35122
    assert "UNKNOWN" in data["facility_index"]["asv_baseline_status"]


@pytest.mark.asyncio
async def test_health_api_v1_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "Dhwani-Sanjeevani Backend"
