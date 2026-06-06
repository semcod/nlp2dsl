"""Tests for trigger-service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "trigger-service"


@pytest.mark.asyncio
async def test_webhook_text_plan() -> None:
    mock_response = {"status": "complete", "workflow": {"name": "test"}}
    with patch("app.main._post_backend", new_callable=AsyncMock, return_value=mock_response):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/triggers/webhook/demo",
                json={"text": "Wyślij raport sprzedaży"},
            )
    assert resp.status_code == 200
    data = resp.json()
    assert data["trigger_id"] == "demo"
    assert data["result"]["status"] == "complete"
