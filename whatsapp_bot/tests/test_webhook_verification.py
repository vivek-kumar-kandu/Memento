import pytest
from fastapi.testclient import TestClient
from config import WHATSAPP_VERIFY_TOKEN


def test_health_check_endpoint(client: TestClient):
    """Verify /health returns healthy status, service name, and backend URL."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "dhwani-sanjeevani-whatsapp-bot"
    assert "backend_base_url" in data
    assert "meta_cloud_api" in data
    assert "session_cache" in data


def test_webhook_verification_success(client: TestClient):
    """Verify Meta challenge verification returns challenge text with HTTP 200 on matching token."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": WHATSAPP_VERIFY_TOKEN,
        "hub.challenge": "1158201444",
    }
    resp = client.get("/webhook", params=params)
    assert resp.status_code == 200
    assert resp.text == "1158201444"


def test_webhook_verification_wrong_token(client: TestClient):
    """Verify Meta challenge verification returns HTTP 403 on invalid token."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "incorrect_hacker_token",
        "hub.challenge": "1158201444",
    }
    resp = client.get("/webhook", params=params)
    assert resp.status_code == 403
    assert "mismatch" in resp.json()["detail"].lower()


def test_webhook_verification_invalid_mode(client: TestClient):
    """Verify Meta challenge verification rejects invalid mode."""
    params = {
        "hub.mode": "publish",
        "hub.verify_token": WHATSAPP_VERIFY_TOKEN,
        "hub.challenge": "1158201444",
    }
    resp = client.get("/webhook", params=params)
    assert resp.status_code == 403


def test_webhook_verification_missing_params(client: TestClient):
    """Verify missing query parameters reject verification."""
    resp = client.get("/webhook")
    assert resp.status_code == 403
