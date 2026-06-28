"""
Stocker — Portfolio Routes
/api/portfolio, /api/trades, /api/trades/open, /api/trades/{trade_id},
/api/portfolio/positions, /api/portfolio/performance
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db, PaperTrade
from backend.paper_trading.engine import get_portfolio_summary
from backend.paper_trading.portfolio import get_open_positions, get_performance_metrics

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
    return get_portfolio_summary(db)


@router.get("/api/portfolio/positions", response_model=None)
def get_positions(db: Session = Depends(get_db)):
    return get_open_positions(db)


@router.get("/api/portfolio/performance", response_model=None)
def get_performance(db: Session = Depends(get_db)):
    return get_performance_metrics(db)


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
