"""
Stocker — Tests for Decision Engine (Phase 5)
Uses an in-memory SQLite DB fixture.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, AgentOutput as AgentOutputModel, Decision as DecisionModel, RawPrice
from backend.schemas.decision import Decision
from backend.agents.decision_engine import decide
from backend.config import AGENT_WEIGHTS


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _insert_agent_output(session, ticker, agent_name, score, confidence=80,
                          created_at=None):
    now = created_at or datetime.utcnow()
    row = AgentOutputModel(
        id=f"{ticker}-{agent_name}-{now.timestamp()}",
        ticker=ticker,
        agent_name=agent_name,
        score=score,
        confidence=confidence,
        signal="BUY" if score >= 60 else "SELL" if score <= 40 else "HOLD",
        reason=f"Test reason for {agent_name} agent output score={score}",
        data_snapshot="{}",
        model_version="test-v1.0",
        created_at=now,
        ticker_price=3500.0,
    )
    session.add(row)
    session.commit()


def _insert_price(session, ticker, close=3500.0):
    row = RawPrice(
        ticker=ticker,
        timestamp=datetime.utcnow(),
        open=close, high=close * 1.01, low=close * 0.99, close=close,
        volume=1_000_000, interval="1d", source="test",
    )
    session.add(row)
    session.commit()


def _make_ollama_response(action="BUY", confidence=75, target=3800.0,
                           stop_loss=3325.0, horizon="medium"):
    payload = {
        "action": action,
        "confidence": confidence,
        "target_price": target,
        "stop_loss": stop_loss,
        "time_horizon": horizon,
        "reason": f"Ollama recommends {action} based on indicators.",
    }
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"response": json.dumps(payload)}
    return mock_resp


# ─────────────────────────────────────────
# Fixture
# ─────────────────────────────────────────

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    _insert_price(session, "TCS.NS")
    yield session
    session.close()


# ─────────────────────────────────────────
# Tests
# ─────────────────────────────────────────

def test_composite_score_weighted_correctly(db_session):
    """Composite must equal weighted sum of the three agent scores."""
    _insert_agent_output(db_session, "TCS.NS", "technical",   80)
    _insert_agent_output(db_session, "TCS.NS", "sentiment",   60)
    _insert_agent_output(db_session, "TCS.NS", "fundamental", 70)

    expected = int(80 * AGENT_WEIGHTS["technical"] +
                   60 * AGENT_WEIGHTS["sentiment"]  +
                   70 * AGENT_WEIGHTS["fundamental"])

    with patch("backend.agents.decision_engine.httpx.post") as mock_post:
        mock_post.return_value = _make_ollama_response()
        result = decide("TCS.NS", db_session)

    assert result.composite_score == expected


def test_ollama_failure_triggers_fallback(db_session):
    """Connection error to Ollama must trigger rule-based fallback."""
    _insert_agent_output(db_session, "TCS.NS", "technical",   60)
    _insert_agent_output(db_session, "TCS.NS", "sentiment",   60)
    _insert_agent_output(db_session, "TCS.NS", "fundamental", 60)

    with patch("backend.agents.decision_engine.httpx.post", side_effect=ConnectionError("no connection")):
        result = decide("TCS.NS", db_session)

    assert isinstance(result, Decision)
    assert "fallback" in result.reason.lower() or "Rule-based" in result.reason


def test_decision_inserted_to_db(db_session):
    """decide() must persist a row in the decisions table."""
    _insert_agent_output(db_session, "TCS.NS", "technical",   65)
    _insert_agent_output(db_session, "TCS.NS", "sentiment",   65)
    _insert_agent_output(db_session, "TCS.NS", "fundamental", 65)

    with patch("backend.agents.decision_engine.httpx.post", side_effect=ConnectionError()):
        decide("TCS.NS", db_session)

    rows = db_session.query(DecisionModel).filter(DecisionModel.ticker == "TCS.NS").all()
    assert len(rows) >= 1


def test_missing_agent_output_uses_50(db_session):
    """No agent outputs → all scores default to 50, still returns a Decision."""
    with patch("backend.agents.decision_engine.httpx.post", side_effect=ConnectionError()):
        result = decide("MISSING.NS", db_session)

    assert isinstance(result, Decision)
    assert result.composite_score is not None
    assert result.technical_score == 50
    assert result.sentiment_score == 50
    assert result.fundamental_score == 50


def test_buy_decision_on_high_scores(db_session):
    """All-80 scores with Ollama returning BUY → action must be BUY."""
    for agent in ("technical", "sentiment", "fundamental"):
        _insert_agent_output(db_session, "TCS.NS", agent, 80)

    with patch("backend.agents.decision_engine.httpx.post") as mock_post:
        mock_post.return_value = _make_ollama_response(action="BUY")
        result = decide("TCS.NS", db_session)

    assert result.action == "BUY"


def test_sell_decision_on_low_scores(db_session):
    """All-20 scores with Ollama returning SELL → action must be SELL."""
    for agent in ("technical", "sentiment", "fundamental"):
        _insert_agent_output(db_session, "TCS.NS", agent, 20)

    with patch("backend.agents.decision_engine.httpx.post") as mock_post:
        mock_post.return_value = _make_ollama_response(action="SELL", stop_loss=3000.0)
        result = decide("TCS.NS", db_session)

    assert result.action == "SELL"


def test_stale_agent_output_uses_50(db_session):
    """Agent output older than 60 min must be treated as missing (score=50)."""
    stale_time = datetime.utcnow() - timedelta(hours=2)
    _insert_agent_output(db_session, "TCS.NS", "technical",   90, created_at=stale_time)
    _insert_agent_output(db_session, "TCS.NS", "sentiment",   60)
    _insert_agent_output(db_session, "TCS.NS", "fundamental", 60)

    with patch("backend.agents.decision_engine.httpx.post", side_effect=ConnectionError()):
        result = decide("TCS.NS", db_session)

    # Stale technical score should have been replaced with 50
    assert result.technical_score == 50
