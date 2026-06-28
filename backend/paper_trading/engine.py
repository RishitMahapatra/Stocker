"""
Stocker — Paper Trading Engine
Opens, closes, and monitors simulated trades based on approved decisions.
"""

from datetime import datetime
from typing import Optional

from backend.config import PAPER_CAPITAL, MAX_POSITION_PCT
from backend.database import PaperTrade, Decision as DecisionModel
from backend.data.fetcher import fetch_current_price


def _deployed_capital(db_session) -> float:
    """Sum of entry_price * quantity for all OPEN trades."""
    open_trades = (
        db_session.query(PaperTrade)
        .filter(PaperTrade.status == "OPEN")
        .all()
    )
    return sum((t.entry_price or 0.0) * (t.quantity or 0) for t in open_trades)


def open_trade(decision, db_session) -> Optional[PaperTrade]:
    """
    Open a new paper trade for an approved BUY decision, or close an existing
    one for a SELL decision. Returns the PaperTrade row or None.
    """
    try:
        if not decision.risk_approved:
            print(f"[engine] Decision not risk-approved for {decision.ticker} — skipping")
            return None

        if decision.action == "HOLD":
            print(f"[engine] HOLD for {decision.ticker} — no trade action")
            return None

        if decision.action == "SELL":
            open_trade_row = (
                db_session.query(PaperTrade)
                .filter(
                    PaperTrade.ticker == decision.ticker,
                    PaperTrade.status == "OPEN",
                )
                .order_by(PaperTrade.entered_at.desc())
                .first()
            )
            if open_trade_row:
                return close_trade(
                    open_trade_row, decision.ticker_price, "MANUAL", db_session
                )
            print(f"[engine] SELL for {decision.ticker} — no open trade found")
            return None

        # BUY path
        if decision.action != "BUY":
            print(f"[engine] Unknown action {decision.action!r} — skipping")
            return None

        # Step 1 — Calculate position size
        deployed = _deployed_capital(db_session)
        available_capital = PAPER_CAPITAL - deployed
        position_value = min(PAPER_CAPITAL * MAX_POSITION_PCT, available_capital)

        if decision.ticker_price is None or decision.ticker_price <= 0:
            print(f"[engine] Invalid ticker_price for {decision.ticker} — skipping")
            return None

        quantity = int(position_value / decision.ticker_price)
        if quantity == 0:
            print(f"[engine] Insufficient capital to buy {decision.ticker} — skipping")
            return None

        print(f"[engine] Opening BUY trade: {decision.ticker} x{quantity} "
              f"@ ₹{decision.ticker_price:.2f} (value ₹{position_value:.2f})")

        # Step 2 & 3 — Create and insert PaperTrade
        trade = PaperTrade(
            decision_id=decision.id,
            ticker=decision.ticker,
            action="BUY",
            quantity=quantity,
            entry_price=decision.ticker_price,
            stop_loss_price=decision.stop_loss,
            target_price=decision.target_price,
            status="OPEN",
            entered_at=datetime.utcnow(),
        )
        db_session.add(trade)
        db_session.commit()
        db_session.refresh(trade)

        print(f"[engine] Trade opened: id={trade.id} ticker={trade.ticker}")
        return trade

    except Exception as e:
        print(f"[engine] open_trade error for {decision.ticker}: {e}")
        return None


def close_trade(trade: PaperTrade, exit_price: float,
                exit_reason: str, db_session) -> PaperTrade:
    """
    Mark a trade as CLOSED and compute PnL.
    exit_reason: "TARGET" | "STOP_LOSS" | "MANUAL"
    """
    try:
        entry  = trade.entry_price or 0.0
        qty    = trade.quantity or 0

        pnl     = (exit_price - entry) * qty
        pnl_pct = ((exit_price - entry) / entry * 100) if entry else 0.0

        trade.status     = "CLOSED"
        trade.exit_price = exit_price
        trade.exit_reason = exit_reason
        trade.exited_at  = datetime.utcnow()
        trade.pnl        = round(pnl, 2)
        trade.pnl_pct    = round(pnl_pct, 4)

        db_session.commit()
        db_session.refresh(trade)

        print(f"[engine] Trade CLOSED: {trade.ticker} | reason={exit_reason} "
              f"| pnl=₹{pnl:.2f} ({pnl_pct:.2f}%)")
        return trade

    except Exception as e:
        print(f"[engine] close_trade error for trade id={trade.id}: {e}")
        return trade


def check_and_update_open_trades(db_session) -> list:
    """
    Fetch current prices for all OPEN trades and close any that have hit
    their stop-loss or target price.
    Returns a list of trades that were closed in this call.
    """
    closed = []
    try:
        open_trades = (
            db_session.query(PaperTrade)
            .filter(PaperTrade.status == "OPEN")
            .all()
        )
        print(f"[engine] Checking {len(open_trades)} open trades ...")

        for trade in open_trades:
            try:
                current_price = fetch_current_price(trade.ticker)
                if current_price is None:
                    print(f"[engine] No price for {trade.ticker} — skipping")
                    continue

                # Check stop loss
                if (trade.stop_loss_price is not None
                        and current_price <= trade.stop_loss_price):
                    print(f"[engine] Stop-loss hit for {trade.ticker}: "
                          f"{current_price} <= {trade.stop_loss_price}")
                    closed_trade = close_trade(trade, current_price, "STOP_LOSS", db_session)
                    closed.append(closed_trade)
                    continue

                # Check target
                if (trade.target_price is not None
                        and current_price >= trade.target_price):
                    print(f"[engine] Target hit for {trade.ticker}: "
                          f"{current_price} >= {trade.target_price}")
                    closed_trade = close_trade(trade, current_price, "TARGET", db_session)
                    closed.append(closed_trade)

            except Exception as e:
                print(f"[engine] Error checking trade id={trade.id}: {e}")

    except Exception as e:
        print(f"[engine] check_and_update_open_trades error: {e}")

    return closed


def get_portfolio_summary(db_session) -> dict:
    """Return a comprehensive portfolio summary dict."""
    try:
        all_trades    = db_session.query(PaperTrade).all()
        open_trades   = [t for t in all_trades if t.status == "OPEN"]
        closed_trades = [t for t in all_trades if t.status == "CLOSED"]

        deployed_capital  = sum((t.entry_price or 0.0) * (t.quantity or 0)
                                for t in open_trades)
        available_capital = PAPER_CAPITAL - deployed_capital
        deployed_pct      = (deployed_capital / PAPER_CAPITAL * 100) if PAPER_CAPITAL else 0.0

        closed_pnls    = [t.pnl for t in closed_trades if t.pnl is not None]
        total_pnl      = sum(closed_pnls)
        winning_trades = sum(1 for p in closed_pnls if p > 0)
        losing_trades  = sum(1 for p in closed_pnls if p < 0)
        win_rate       = (winning_trades / len(closed_trades) * 100) if closed_trades else 0.0
        best_trade     = max(closed_pnls) if closed_pnls else None
        worst_trade    = min(closed_pnls) if closed_pnls else None

        return {
            "total_capital":    PAPER_CAPITAL,
            "deployed_capital": round(deployed_capital, 2),
            "available_capital": round(available_capital, 2),
            "deployed_pct":     round(deployed_pct, 2),
            "open_positions":   len(open_trades),
            "total_trades":     len(all_trades),
            "closed_trades":    len(closed_trades),
            "total_pnl":        round(total_pnl, 2),
            "winning_trades":   winning_trades,
            "losing_trades":    losing_trades,
            "win_rate":         round(win_rate, 2),
            "best_trade":       round(best_trade, 2) if best_trade is not None else None,
            "worst_trade":      round(worst_trade, 2) if worst_trade is not None else None,
        }

    except Exception as e:
        print(f"[engine] get_portfolio_summary error: {e}")
        return {
            "total_capital":    PAPER_CAPITAL,
            "deployed_capital": 0.0,
            "available_capital": PAPER_CAPITAL,
            "deployed_pct":     0.0,
            "open_positions":   0,
            "total_trades":     0,
            "closed_trades":    0,
            "total_pnl":        0.0,
            "winning_trades":   0,
            "losing_trades":    0,
            "win_rate":         0.0,
            "best_trade":       None,
            "worst_trade":      None,
        }
