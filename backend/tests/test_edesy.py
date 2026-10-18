import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_edesy_tool_endpoint_turn1():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/tool",
            json={
                "call_sid": "edesy-test-call-101",
                "transcript": "Help, snake bit my hand in Lucknow!",
                "caller_phone": "+919876543210",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "response_text" in data
        assert data["next_action"] in ["COLLECT_LOCATION", "DISPATCH_OR_TRANSPORT", "CONTINUE"]
        assert data["conversation_id"] is not None
        assert data["case_id"] is not None
        assert data["end_call"] is False


@pytest.mark.asyncio
async def test_edesy_webhook_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/edesy/webhook",
            json={
                "call_sid": "edesy-test-call-101",
                "event_type": "call.ended",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "received"
        assert data["call_sid"] == "edesy-test-call-101"
