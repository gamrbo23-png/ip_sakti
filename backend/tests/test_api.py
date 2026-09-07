"""
Unit and Integration Tests for IP-SAKTI Sahayak Backend API
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_domains_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/domains")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert len(data["domains"]) >= 8


@pytest.mark.asyncio
async def test_chat_validation_empty_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/chat", json={"query": ""})
        assert response.status_code == 422 or response.status_code == 400


@pytest.mark.asyncio
async def test_feedback_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/feedback",
            json={
                "rating": 1,
                "comment": "Very accurate citation",
            },
        )
        assert response.status_code == 200
        assert "id" in response.json()
