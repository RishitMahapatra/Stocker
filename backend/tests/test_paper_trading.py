"""
Stocker — Tests for Paper Trading Engine (Phase 7)
Uses an in-memory SQLite DB fixture.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, PaperTrade, Decision as DecisionModel
from backend.paper_trading.engine import (
    open_trade, close_trade, check_and_update_open_trades, get_portfolio_summary,
)
from backend.config import PAPER_CAPITAL, MAX_POSITION_PCT


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _make_decision(session, ticker="TCS.NS", action="BUY", ticker_price=1000.0,
                   stop_loss=950.0, target_price=1200.0, risk_approved=True):
    """Insert a Decision row and return a SimpleNamespace mirroring its fields."""
    now = datetime.utcnow()
    db_row = DecisionModel(
        ticker=ticker,
        action=action,
        confidence=70,
        composite_score=65,
        technical_score=65,
        sentiment_score=65,
        fundamental_score=65,
        target_price=target_price,
        stop_loss=stop_loss,
        time_horizon="medium",
        reason=f"Test decision {action} {ticker}",
        risk_approved=risk_approved,
        risk_reason=None,
        ollama_raw=None,
        decided_at=now,
        ticker_price=ticker_price,
    )
    session.add(db_row)
    session.commit()
    session.refresh(db_row)

    return SimpleNamespace(
        id=db_row.id,
        ticker=ticker,
        action=action,
        ticker_price=ticker_price,
        stop_loss=stop_loss,
        target_price=target_price,
        risk_approved=risk_approved,
    )


def _insert_open_trade(session, ticker="TCS.NS", entry_price=1000.0,
                        quantity=10, stop_loss_price=950.0, target_price=1200.0):
    trade = PaperTrade(
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price,
        target_price=target_price,
        status="OPEN",
        entered_at=datetime.utcnow(),
    )
    session.add(trade)
    session.commit()
    session.refresh(trade)
    return trade


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

def test_open_trade_on_approved_buy(db_session):
    """Approved BUY decision → trade opened with OPEN status and quantity > 0."""
    decision = _make_decision(db_session, action="BUY", ticker_price=1000.0,
                               risk_approved=True)
    result = open_trade(decision, db_session)

    assert result is not None
    assert result.status == "OPEN"
    assert result.quantity > 0


def test_no_trade_on_unapproved_decision(db_session):
    """Risk-rejected BUY decision → open_trade returns None."""
    decision = _make_decision(db_session, action="BUY", ticker_price=1000.0,
                               risk_approved=False)
    result = open_trade(decision, db_session)
    assert result is None


def test_no_trade_on_hold(db_session):
    """HOLD decision → open_trade returns None, no trade created."""
    decision = _make_decision(db_session, action="HOLD", ticker_price=1000.0,
                               risk_approved=True)
    result = open_trade(decision, db_session)
    assert result is None


def test_close_trade_computes_pnl(db_session):
    """close_trade must compute correct PnL and PnL% and set status to CLOSED."""
    trade = _insert_open_trade(db_session, entry_price=1000.0, quantity=10)
    closed = close_trade(trade, exit_price=1100.0, exit_reason="MANUAL",
                          db_session=db_session)

    assert closed.pnl == 1000.0        # (1100 - 1000) * 10
    assert closed.pnl_pct == 10.0      # (1100 - 1000) / 1000 * 100
    assert closed.status == "CLOSED"
    assert closed.exit_reason == "MANUAL"


def test_stop_loss_closes_trade(db_session):
    """Price below stop_loss_price → trade closed with exit_reason='STOP_LOSS'."""
    trade = _insert_open_trade(db_session, entry_price=1000.0,
                                stop_loss_price=950.0, quantity=5)

    with patch("backend.paper_trading.engine.fetch_current_price", return_value=940.0):
        closed_list = check_and_update_open_trades(db_session)

    assert len(closed_list) == 1
    assert closed_list[0].exit_reason == "STOP_LOSS"
    assert closed_list[0].status == "CLOSED"


def test_target_closes_trade(db_session):
    """Price at or above target_price → trade closed with exit_reason='TARGET'."""
    trade = _insert_open_trade(db_session, entry_price=1000.0,
                                target_price=1200.0, quantity=5)

    with patch("backend.paper_trading.engine.fetch_current_price", return_value=1250.0):
        closed_list = check_and_update_open_trades(db_session)

    assert len(closed_list) == 1
    assert closed_list[0].exit_reason == "TARGET"
    assert closed_list[0].status == "CLOSED"


def test_portfolio_summary_keys(db_session):
    """get_portfolio_summary must return a dict with all required keys."""
    summary = get_portfolio_summary(db_session)
    required = {
        "total_capital", "deployed_capital", "available_capital",
        "deployed_pct", "total_pnl", "win_rate",
    }
    assert required.issubset(summary.keys())


def test_position_size_respects_max_pct(db_session):
    """Quantity must not exceed MAX_POSITION_PCT * PAPER_CAPITAL / ticker_price."""
    decision = _make_decision(db_session, action="BUY", ticker_price=500.0,
                               risk_approved=True)
    result = open_trade(decision, db_session)

    max_qty = int(PAPER_CAPITAL * MAX_POSITION_PCT / 500.0)
    assert result is not None
    assert result.quantity <= max_qty
