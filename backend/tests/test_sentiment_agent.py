"""
Stocker — Tests for Sentiment Analysis Agent (Phase 3)
Uses an in-memory SQLite DB fixture with seeded raw_news data.
"""

import json
import random
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, RawNews, RawPrice
from backend.schemas.agent import AgentOutput
from backend.agents.sentiment_agent import analyze


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _seed_news(session, ticker: str, n: int = 25, hours_back: float = 48.0):
    """Insert n fake headlines with random VADER scores for ticker."""
    random.seed(7)
    now = datetime.utcnow()
    for i in range(n):
        pub = now - timedelta(hours=random.uniform(0, hours_back))
        row = RawNews(
            ticker=ticker,
            headline=f"Test headline {i} for {ticker}",
            source="test",
            url=f"http://example.com/{i}",
            published_at=pub,
            vader_score=random.uniform(-1.0, 1.0),
            fetched_at=now,
        )
        session.add(row)
    session.commit()


def _seed_price(session, ticker: str, close: float = 3500.0):
    row = RawPrice(
        ticker=ticker,
        timestamp=datetime.utcnow(),
        open=close,
        high=close * 1.01,
        low=close * 0.99,
        close=close,
        volume=1_000_000,
        interval="1d",
        source="test",
    )
    session.add(row)
    session.commit()


# ─────────────────────────────────────────
# Fixture
# ─────────────────────────────────────────

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    _seed_news(session, "TCS.NS", n=25)
    _seed_price(session, "TCS.NS", close=3500.0)

    yield session
    session.close()


# ─────────────────────────────────────────
# Tests
# ─────────────────────────────────────────

def test_sentiment_returns_agent_output(db_session):
    """analyze() must return an AgentOutput instance."""
    result = analyze("TCS.NS", db_session)
    assert isinstance(result, AgentOutput)


def test_sentiment_score_in_range(db_session):
    """score must be between 0 and 100 inclusive."""
    result = analyze("TCS.NS", db_session)
    assert 0 <= result.score <= 100


def test_sentiment_signal_matches_score(db_session):
    """signal must match the score against config thresholds."""
    result = analyze("TCS.NS", db_session)
    if result.score >= 60:
        assert result.signal == "BUY"
    elif result.score <= 40:
        assert result.signal == "SELL"
    else:
        assert result.signal == "HOLD"


def test_sentiment_no_news_returns_hold(db_session):
    """No news for ticker → HOLD with confidence == 0."""
    result = analyze("FAKE.NS", db_session)
    assert result.signal == "HOLD"
    assert result.confidence == 0


def test_time_decay_reduces_old_headline_weight(db_session):
    """
    Recent strongly positive headline should dominate over an old negative one,
    producing a score above 50.
    """
    now = datetime.utcnow()
    ticker = "DECAY.NS"

    db_session.add(RawNews(
        ticker=ticker,
        headline="Very good news right now",
        source="test",
        published_at=now - timedelta(hours=1),
        vader_score=1.0,
        fetched_at=now,
    ))
    db_session.add(RawNews(
        ticker=ticker,
        headline="Very bad news long ago",
        source="test",
        published_at=now - timedelta(hours=100),
        vader_score=-1.0,
        fetched_at=now,
    ))
    db_session.commit()

    result = analyze(ticker, db_session)
    assert result.score > 50


def test_confidence_scales_with_headline_count(db_session):
    """25 headlines → confidence band == 90."""
    result = analyze("TCS.NS", db_session)
    assert result.confidence == 90


def test_data_snapshot_has_required_keys(db_session):
    """data_snapshot JSON must contain all required keys."""
    result = analyze("TCS.NS", db_session)
    snapshot = json.loads(result.data_snapshot)
    required = {
        "headlines_count",
        "weighted_score",
        "oldest_headline_hours",
        "newest_headline_hours",
        "avg_raw_vader",
        "confidence_band",
    }
    assert required.issubset(snapshot.keys())


def test_agent_name_is_sentiment(db_session):
    """agent_name must equal 'sentiment'."""
    result = analyze("TCS.NS", db_session)
    assert result.agent_name == "sentiment"
