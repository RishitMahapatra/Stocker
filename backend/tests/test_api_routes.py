"""
Stocker — Tests for FastAPI Routes (Phase 6)
Uses FastAPI TestClient with mocked scheduler.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(scope="module")
def client():
    """
    Create a TestClient with scheduler patched out so tests don't
    attempt real DB writes or network calls on startup.
    """
    mock_scheduler = MagicMock()
    mock_scheduler.running = False

    with patch("backend.scheduler.start_scheduler", return_value=mock_scheduler), \
         patch("backend.scheduler.run_full_pipeline", new_callable=lambda: lambda: AsyncMock()), \
         patch("asyncio.create_task", return_value=None):

        from backend.main import app
        from fastapi.testclient import TestClient

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_health_endpoint(client):
    """GET /health must return 200 with status='ok'."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "time" in data


def test_tickers_endpoint(client):
    """GET /api/tickers must return all 10 configured tickers."""
    resp = client.get("/api/tickers")
    assert resp.status_code == 200
    data = resp.json()
    assert "tickers" in data
    assert len(data["tickers"]) == 10


def test_prices_endpoint(client):
    """GET /api/prices/TCS.NS must return 200 with a list, or 404 if no data."""
    resp = client.get("/api/prices/TCS.NS")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


def test_signals_endpoint(client):
    """GET /api/signals must return 200 with a list."""
    resp = client.get("/api/signals")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_single_ticker_signal(client):
    """GET /api/signals/TCS.NS must return 200 with expected key, or 404."""
    resp = client.get("/api/signals/TCS.NS")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        body = resp.json()
        assert "ticker" in body or "decision" in body


def test_portfolio_endpoint(client):
    """GET /api/portfolio must return 200 with required keys."""
    resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_capital" in data
    assert "deployed_pct" in data


def test_404_for_unknown_ticker(client):
    """GET /api/prices/FAKE.NS must return 404."""
    resp = client.get("/api/prices/FAKE.NS")
    assert resp.status_code == 404


def test_trades_endpoint(client):
    """GET /api/trades must return 200 with a list."""
    resp = client.get("/api/trades")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
