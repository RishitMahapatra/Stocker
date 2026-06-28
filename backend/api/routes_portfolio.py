"""
Stocker — Portfolio Routes
/api/portfolio, /api/trades, /api/trades/open, /api/trades/{trade_id}
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.config import PAPER_CAPITAL
from backend.database import get_db, PaperTrade

router = APIRouter()


def _trade_to_dict(t) -> dict:
    return {
        "id":               t.id,
        "decision_id":      t.decision_id,
        "ticker":           t.ticker,
        "action":           t.action,
        "quantity":         t.quantity,
        "entry_price":      t.entry_price,
        "stop_loss_price":  t.stop_loss_price,
        "target_price":     t.target_price,
        "status":           t.status,
        "exit_price":       t.exit_price,
        "exit_reason":      t.exit_reason,
        "pnl":              t.pnl,
        "pnl_pct":          t.pnl_pct,
        "entered_at":       t.entered_at.isoformat() if t.entered_at else None,
        "exited_at":        t.exited_at.isoformat() if t.exited_at else None,
    }


@router.get("/api/portfolio", response_model=None)
def get_portfolio(db: Session = Depends(get_db)):
    all_trades  = db.query(PaperTrade).all()
    open_trades = [t for t in all_trades if t.status == "OPEN"]
    closed      = [t for t in all_trades if t.status != "OPEN"]

    deployed_capital = sum(
        (t.entry_price or 0.0) * (t.quantity or 0) for t in open_trades
    )
    available_capital = PAPER_CAPITAL - deployed_capital
    deployed_pct      = (deployed_capital / PAPER_CAPITAL * 100) if PAPER_CAPITAL else 0.0

    total_pnl   = sum(t.pnl or 0.0 for t in closed)
    winning     = [t for t in closed if (t.pnl or 0.0) > 0]
    win_rate    = (len(winning) / len(closed) * 100) if closed else 0.0

    return {
        "total_capital":    PAPER_CAPITAL,
        "deployed_capital": round(deployed_capital, 2),
        "available_capital": round(available_capital, 2),
        "deployed_pct":     round(deployed_pct, 2),
        "open_positions":   len(open_trades),
        "total_trades":     len(all_trades),
        "total_pnl":        round(total_pnl, 2),
        "win_rate":         round(win_rate, 2),
    }


@router.get("/api/trades", response_model=None)
def get_all_trades(db: Session = Depends(get_db)):
    rows = db.query(PaperTrade).order_by(PaperTrade.entered_at.desc()).all()
    return [_trade_to_dict(t) for t in rows]


@router.get("/api/trades/open", response_model=None)
def get_open_trades(db: Session = Depends(get_db)):
    rows = (
        db.query(PaperTrade)
        .filter(PaperTrade.status == "OPEN")
        .order_by(PaperTrade.entered_at.desc())
        .all()
    )
    return [_trade_to_dict(t) for t in rows]


@router.get("/api/trades/{trade_id}", response_model=None)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
    if trade is None:
        raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")
    return _trade_to_dict(trade)
