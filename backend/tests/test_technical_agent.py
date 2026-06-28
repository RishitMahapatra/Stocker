"""
Stocker — Tests for Technical Analysis Agent (Phase 2)
Uses an in-memory SQLite DB fixture with seeded raw_prices data.
"""

import json
import math
import random
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, RawPrice
from backend.schemas.agent import AgentOutput
from backend.agents.technical_agent import (
    _rsi_vote, _macd_vote, _ema_vote, analyze,
)
from backend.data.feature_engineer import compute_features


# ─────────────────────────────────────────
# Fixture: in-memory SQLite DB seeded with TCS.NS price data
# ─────────────────────────────────────────

def _seed_prices(session, ticker: str, n: int = 250, base_price: float = 3500.0):
    """Insert n daily OHLCV rows for ticker into raw_prices."""
    random.seed(42)
    price = base_price
    start = datetime(2024, 1, 1)
    for i in range(n):
        change = random.uniform(-0.02, 0.025)
        price = max(price * (1 + change), 100.0)
        o = price * random.uniform(0.99, 1.01)
        h = max(price, o) * random.uniform(1.0, 1.015)
        l = min(price, o) * random.uniform(0.985, 1.0)
        row = RawPrice(
            ticker=ticker,
            timestamp=start + timedelta(days=i),
            open=round(o, 2),
            high=round(h, 2),
            low=round(l, 2),
            close=round(price, 2),
            volume=random.randint(500_000, 5_000_000),
            interval="1d",
            source="test",
        )
        session.add(row)
    session.commit()


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    _seed_prices(session, "TCS.NS", n=250, base_price=3500.0)

    yield session
    session.close()


# ─────────────────────────────────────────
# Tests
# ─────────────────────────────────────────

def test_features_computed_for_ticker(db_session):
    """compute_features returns a dict containing rsi_14."""
    result = compute_features("TCS.NS", db_session)
    assert isinstance(result, dict)
    assert "rsi_14" in result


def test_rsi_scoring_bullish():
    """RSI below 30 should produce vote of +1."""
    vote = _rsi_vote(25)
    assert vote == 1


def test_rsi_scoring_bearish():
    """RSI above 70 should produce vote of -1."""
    vote = _rsi_vote(75)
    assert vote == -1


def test_macd_scoring():
    """MACD line above signal with positive histogram should produce vote +1."""
    vote = _macd_vote(macd_line=10, macd_signal=5, macd_histogram=5)
    assert vote == 1


def test_ema_trend_scoring():
    """price > ema_20 > ema_50 > ema_200 should produce EMA vote +1."""
    vote = _ema_vote(price=200, ema_20=190, ema_50=180, ema_200=170)
    assert vote == 1


def test_score_in_range_0_to_100(db_session):
    """analyze() for TCS.NS must return a score between 0 and 100 inclusive."""
    output = analyze("TCS.NS", db_session)
    assert 0 <= output.score <= 100


def test_signal_matches_score(db_session):
    """signal must match the score thresholds from config."""
    output = analyze("TCS.NS", db_session)
    if output.score >= 60:
        assert output.signal == "BUY"
    elif output.score <= 40:
        assert output.signal == "SELL"
    else:
        assert output.signal == "HOLD"


def test_output_schema_valid(db_session):
    """analyze() must return a valid AgentOutput with agent_name == 'technical'."""
    output = analyze("TCS.NS", db_session)
    assert isinstance(output, AgentOutput)
    assert output.agent_name == "technical"


def test_insufficient_data_returns_hold(db_session):
    """analyze() for an unknown ticker returns HOLD with confidence == 0."""
    output = analyze("FAKE.NS", db_session)
    assert output.signal == "HOLD"
    assert output.confidence == 0
