"""
Stocker — Tests for Fundamental Analysis Agent (Phase 4)
Uses an in-memory SQLite DB fixture with seeded raw_fundamentals data.
"""

import json
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, RawFundamental, RawPrice
from backend.schemas.agent import AgentOutput
from backend.agents.fundamental_agent import analyze, _score_pe, _score_debt
from backend.config import PE_GOOD_MAX, PE_ACCEPTABLE_MAX


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _seed_fundamental(session, ticker: str, **kwargs):
    defaults = dict(
        pe_ratio=22.0,
        revenue_growth=0.18,
        profit_margin=0.20,
        debt_to_equity=0.3,
        roe=0.20,
        eps=50.0,
        market_cap=1_000_000_000,
        dividend_yield=0.02,
        price_to_book=2.5,
        sector="IT",
        fetched_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    row = RawFundamental(ticker=ticker, **defaults)
    session.add(row)
    session.commit()
    return row


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

    _seed_fundamental(session, "TCS.NS")
    _seed_price(session, "TCS.NS", close=3500.0)

    yield session
    session.close()


# ─────────────────────────────────────────
# Tests
# ─────────────────────────────────────────

def test_fundamental_returns_agent_output(db_session):
    """analyze() must return an AgentOutput instance."""
    result = analyze("TCS.NS", db_session)
    assert isinstance(result, AgentOutput)


def test_fundamental_score_in_range(db_session):
    """score must be between 0 and 100 inclusive."""
    result = analyze("TCS.NS", db_session)
    assert 0 <= result.score <= 100


def test_fundamental_signal_matches_score(db_session):
    """signal must match the score against config thresholds."""
    result = analyze("TCS.NS", db_session)
    if result.score >= 60:
        assert result.signal == "BUY"
    elif result.score <= 40:
        assert result.signal == "SELL"
    else:
        assert result.signal == "HOLD"


def test_no_fundamentals_returns_hold(db_session):
    """No fundamental data → HOLD with confidence == 0."""
    result = analyze("FAKE.NS", db_session)
    assert result.signal == "HOLD"
    assert result.confidence == 0


def test_pe_scoring_good():
    """PE below PE_GOOD_MAX (25) should score +1."""
    assert _score_pe(20) == 1


def test_pe_scoring_bad():
    """PE above PE_ACCEPTABLE_MAX (40) should score -1."""
    assert _score_pe(50) == -1


def test_high_debt_lowers_score(db_session):
    """Very high D/E ratio should produce a lower score than a low D/E ticker."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    _seed_fundamental(session, "HIGHDEBT.NS", debt_to_equity=5.0)
    _seed_fundamental(session, "LOWDEBT.NS", debt_to_equity=0.1)

    high_debt_result = analyze("HIGHDEBT.NS", session)
    low_debt_result  = analyze("LOWDEBT.NS", session)

    assert high_debt_result.score < low_debt_result.score
    session.close()


def test_all_good_metrics_gives_high_score(db_session):
    """All strongly positive metrics should produce score >= 60 and BUY signal."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    _seed_fundamental(session, "GREAT.NS",
        pe_ratio=15.0,
        revenue_growth=0.25,
        profit_margin=0.22,
        debt_to_equity=0.2,
        roe=0.25,
    )
    result = analyze("GREAT.NS", session)
    assert result.score >= 60
    assert result.signal == "BUY"
    session.close()


def test_all_bad_metrics_gives_low_score(db_session):
    """All strongly negative metrics should produce score <= 40 and SELL signal."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    _seed_fundamental(session, "BAD.NS",
        pe_ratio=60.0,
        revenue_growth=-0.10,
        profit_margin=0.02,
        debt_to_equity=2.0,
        roe=0.04,
    )
    result = analyze("BAD.NS", session)
    assert result.score <= 40
    assert result.signal == "SELL"
    session.close()


def test_confidence_full_metrics(db_session):
    """All 5 metrics present → confidence == 90."""
    result = analyze("TCS.NS", db_session)
    assert result.confidence == 90


def test_confidence_missing_metrics(db_session):
    """Only 2 metrics present → confidence == 40."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    _seed_fundamental(session, "SPARSE.NS",
        pe_ratio=20.0,
        revenue_growth=0.10,
        profit_margin=None,
        debt_to_equity=None,
        roe=None,
    )
    result = analyze("SPARSE.NS", session)
    assert result.confidence == 40
    session.close()


def test_data_snapshot_has_required_keys(db_session):
    """data_snapshot JSON must contain all required keys."""
    result = analyze("TCS.NS", db_session)
    snapshot = json.loads(result.data_snapshot)
    required = {
        "pe_ratio", "revenue_growth", "profit_margin", "debt_to_equity", "roe",
        "pe_score", "revenue_score", "margin_score", "debt_score", "roe_score",
        "weighted_sum", "metrics_available",
    }
    assert required.issubset(snapshot.keys())


def test_agent_name_is_fundamental(db_session):
    """agent_name must equal 'fundamental'."""
    result = analyze("TCS.NS", db_session)
    assert result.agent_name == "fundamental"
