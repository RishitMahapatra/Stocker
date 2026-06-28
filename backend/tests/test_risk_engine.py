"""
Stocker — Tests for Risk Engine (Phase 5)
Uses an in-memory SQLite DB fixture.
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, Decision as DecisionModel, PaperTrade
from backend.schemas.decision import Decision as DecisionSchema
from backend.agents.risk_engine import validate
from backend.config import PAPER_CAPITAL, MAX_POSITION_PCT


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _make_decision(session, ticker="TCS.NS", action="BUY", stop_loss=3325.0,
                   composite=65, price=3500.0) -> DecisionSchema:
    """Insert a Decision row and return the Pydantic schema object."""
    now = datetime.utcnow()
    db_row = DecisionModel(
        ticker=ticker,
        action=action,
        confidence=70,
        composite_score=composite,
        technical_score=65,
        sentiment_score=65,
        fundamental_score=65,
        target_price=None,
        stop_loss=stop_loss,
        time_horizon="medium",
        reason=f"Test decision for {ticker} action={action}",
        risk_approved=False,
        risk_reason=None,
        ollama_raw=None,
        decided_at=now,
        ticker_price=price,
    )
    session.add(db_row)
    session.commit()
    session.refresh(db_row)

    return DecisionSchema(
        id=db_row.id,
        ticker=ticker,
        action=action,
        confidence=70,
        composite_score=composite,
        technical_score=65,
        sentiment_score=65,
        fundamental_score=65,
        target_price=None,
        stop_loss=stop_loss,
        time_horizon="medium",
        reason=f"Test decision for {ticker} action={action}",
        risk_approved=False,
        risk_reason=None,
        ollama_raw=None,
        decided_at=now,
        ticker_price=price,
    )


def _open_trade(session, ticker="TCS.NS", entry_price=3500.0, quantity=10,
                pnl=None):
    row = PaperTrade(
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        entry_price=entry_price,
        stop_loss_price=entry_price * 0.95,
        status="OPEN",
        pnl=pnl,
        entered_at=datetime.utcnow(),
    )
    session.add(row)
    session.commit()


# ─────────────────────────────────────────
# Fixture
# ─────────────────────────────────────────

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ─────────────────────────────────────────
# Tests
# ─────────────────────────────────────────

def test_valid_decision_gets_approved(db_session):
    """BUY with valid stop_loss and empty portfolio → approved."""
    decision = _make_decision(db_session, action="BUY", stop_loss=3325.0)
    result = validate(decision, db_session)
    assert result.risk_approved is True


def test_position_size_limit_enforced(db_session):
    """Near-fully-deployed portfolio → BUY rejected for exceeding max position."""
    # Deploy enough capital so deployed_pct + MAX_POSITION_PCT > 1.0
    # MAX_POSITION_PCT = 0.10, PAPER_CAPITAL = 1_000_000
    # So we need deployed > 90% of capital = 900_000
    big_trade_value = PAPER_CAPITAL * (1.0 - MAX_POSITION_PCT + 0.01)
    qty = 1
    entry = big_trade_value / qty
    _open_trade(db_session, ticker="RELIANCE.NS", entry_price=entry, quantity=qty)

    decision = _make_decision(db_session, ticker="TCS.NS", action="BUY", stop_loss=3325.0)
    result = validate(decision, db_session)

    assert result.risk_approved is False
    assert "deployed" in result.risk_reason.lower()


def test_duplicate_position_rejected(db_session):
    """Open trade already exists for TCS.NS → BUY rejected."""
    _open_trade(db_session, ticker="TCS.NS", entry_price=3500.0, quantity=5)
    decision = _make_decision(db_session, ticker="TCS.NS", action="BUY", stop_loss=3325.0)
    result = validate(decision, db_session)

    assert result.risk_approved is False
    assert "open position" in result.risk_reason.lower()


def test_max_drawdown_blocks_buy(db_session):
    """Portfolio drawdown exceeding MAX_DRAWDOWN_LIMIT → BUY rejected."""
    # Simulate realised losses > 15% of PAPER_CAPITAL
    big_loss = -(PAPER_CAPITAL * 0.20)
    _open_trade(db_session, ticker="WIPRO.NS", entry_price=500.0,
                quantity=1, pnl=big_loss)

    decision = _make_decision(db_session, ticker="TCS.NS", action="BUY", stop_loss=3325.0)
    result = validate(decision, db_session)

    assert result.risk_approved is False
    assert "drawdown" in result.risk_reason.lower()


def test_sell_always_approved(db_session):
    """SELL decision must always be approved regardless of portfolio state."""
    # Fill portfolio so a BUY would be rejected
    big_trade = PAPER_CAPITAL * 0.95
    _open_trade(db_session, ticker="TCS.NS", entry_price=big_trade, quantity=1)

    decision = _make_decision(db_session, ticker="TCS.NS", action="SELL", stop_loss=3325.0)
    result = validate(decision, db_session)

    assert result.risk_approved is True


def test_hold_always_approved(db_session):
    """HOLD decision must always be approved."""
    decision = _make_decision(db_session, ticker="TCS.NS", action="HOLD", stop_loss=3325.0)
    result = validate(decision, db_session)
    assert result.risk_approved is True


def test_risk_reason_populated_on_rejection(db_session):
    """Any rejection must populate a non-empty risk_reason."""
    _open_trade(db_session, ticker="TCS.NS", entry_price=3500.0, quantity=5)
    decision = _make_decision(db_session, ticker="TCS.NS", action="BUY", stop_loss=3325.0)
    result = validate(decision, db_session)

    assert result.risk_approved is False
    assert result.risk_reason is not None
    assert len(result.risk_reason) > 0
