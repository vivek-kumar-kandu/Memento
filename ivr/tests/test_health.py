import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure ivr directory is in sys.path
_IVR_DIR = Path(__file__).resolve().parent.parent
if str(_IVR_DIR) not in sys.path:
    sys.path.insert(0, str(_IVR_DIR))

from main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "sanjeevani-ivr-adapter"
    assert data["version"] == "0.1.0"
    assert "backend_base_url_configured" in data
