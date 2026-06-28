"""
Stocker — Paper Trading Portfolio Analytics
Current positions, trade history, and performance metrics.
"""

from datetime import datetime
from typing import Optional

from backend.database import PaperTrade, Decision as DecisionModel
from backend.data.fetcher import fetch_current_price


def get_open_positions(db_session) -> list:
    """
    Return all OPEN trades enriched with live price and unrealised PnL.
    """
    try:
        trades = (
            db_session.query(PaperTrade)
            .filter(PaperTrade.status == "OPEN")
            .order_by(PaperTrade.entered_at.desc())
            .all()
        )

        results = []
        now = datetime.utcnow()

        for t in trades:
            try:
                current_price = fetch_current_price(t.ticker)
                entry   = t.entry_price or 0.0
                qty     = t.quantity or 0

                if current_price is not None and entry > 0:
                    unrealized_pnl     = round((current_price - entry) * qty, 2)
                    unrealized_pnl_pct = round((current_price - entry) / entry * 100, 4)
                else:
                    unrealized_pnl     = None
                    unrealized_pnl_pct = None

                entered = t.entered_at or now
                days_held = (now - entered).days

                results.append({
                    "id":                t.id,
                    "ticker":            t.ticker,
                    "quantity":          qty,
                    "entry_price":       entry,
                    "current_price":     current_price,
                    "unrealized_pnl":    unrealized_pnl,
                    "unrealized_pnl_pct": unrealized_pnl_pct,
                    "stop_loss_price":   t.stop_loss_price,
                    "target_price":      t.target_price,
                    "entered_at":        entered.isoformat(),
                    "days_held":         days_held,
                })
            except Exception as e:
                print(f"[portfolio] Error enriching trade id={t.id}: {e}")

        return results

    except Exception as e:
        print(f"[portfolio] get_open_positions error: {e}")
        return []


def get_trade_history(db_session, limit: int = 50) -> list:
    """Return the most recent closed trades as plain dicts."""
    try:
        trades = (
            db_session.query(PaperTrade)
            .filter(PaperTrade.status == "CLOSED")
            .order_by(PaperTrade.exited_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id":              t.id,
                "decision_id":     t.decision_id,
                "ticker":          t.ticker,
                "action":          t.action,
                "quantity":        t.quantity,
                "entry_price":     t.entry_price,
                "exit_price":      t.exit_price,
                "exit_reason":     t.exit_reason,
                "pnl":             t.pnl,
                "pnl_pct":         t.pnl_pct,
                "stop_loss_price": t.stop_loss_price,
                "target_price":    t.target_price,
                "status":          t.status,
                "entered_at":      t.entered_at.isoformat() if t.entered_at else None,
                "exited_at":       t.exited_at.isoformat()  if t.exited_at  else None,
            }
            for t in trades
        ]

    except Exception as e:
        print(f"[portfolio] get_trade_history error: {e}")
        return []


def get_performance_metrics(db_session) -> dict:
    """Return aggregated performance statistics across decisions and trades."""
    try:
        all_decisions = db_session.query(DecisionModel).all()
        all_trades    = db_session.query(PaperTrade).all()

        closed = [t for t in all_trades if t.status == "CLOSED"]
        open_  = [t for t in all_trades if t.status == "OPEN"]

        total_decisions = len(all_decisions)
        buy_signals  = sum(1 for d in all_decisions if d.action == "BUY")
        sell_signals = sum(1 for d in all_decisions if d.action == "SELL")
        hold_signals = sum(1 for d in all_decisions if d.action == "HOLD")

        closed_pnls   = [t.pnl for t in closed if t.pnl is not None]
        total_pnl     = sum(closed_pnls)
        winning       = sum(1 for p in closed_pnls if p > 0)
        win_rate      = (winning / len(closed) * 100) if closed else 0.0
        avg_pnl       = (total_pnl / len(closed)) if closed else 0.0

        # Max drawdown: largest peak-to-trough drop in cumulative PnL
        max_drawdown = 0.0
        if closed_pnls:
            peak = 0.0
            running = 0.0
            for pnl in closed_pnls:
                running += pnl
                if running > peak:
                    peak = running
                drawdown = peak - running
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return {
            "total_decisions":    total_decisions,
            "buy_signals":        buy_signals,
            "sell_signals":       sell_signals,
            "hold_signals":       hold_signals,
            "total_trades":       len(all_trades),
            "open_trades":        len(open_),
            "closed_trades":      len(closed),
            "total_pnl":          round(total_pnl, 2),
            "win_rate":           round(win_rate, 2),
            "avg_pnl_per_trade":  round(avg_pnl, 2),
            "max_drawdown":       round(max_drawdown, 2),
        }

    except Exception as e:
        print(f"[portfolio] get_performance_metrics error: {e}")
        return {
            "total_decisions": 0, "buy_signals": 0, "sell_signals": 0,
            "hold_signals": 0, "total_trades": 0, "open_trades": 0,
            "closed_trades": 0, "total_pnl": 0.0, "win_rate": 0.0,
            "avg_pnl_per_trade": 0.0, "max_drawdown": 0.0,
        }
