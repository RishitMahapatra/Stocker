"""
Stocker — Market Data Routes
/api/tickers, /api/prices/{ticker}, /api/prices/{ticker}/latest
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.config import TICKER_LIST
from backend.database import get_db, RawPrice

router = APIRouter()


@router.get("/api/tickers", response_model=None)
def get_tickers():
    return {"tickers": TICKER_LIST}


@router.get("/api/prices/{ticker}/latest", response_model=None)
def get_latest_price(ticker: str, db: Session = Depends(get_db)):
    if ticker not in TICKER_LIST:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker!r} not found")

    row = (
        db.query(RawPrice)
        .filter(RawPrice.ticker == ticker)
        .order_by(RawPrice.timestamp.desc())
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"No price data for {ticker!r}")

    return {
        "ticker":    row.ticker,
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        "open":      row.open,
        "high":      row.high,
        "low":       row.low,
        "close":     row.close,
        "volume":    row.volume,
        "interval":  row.interval,
        "source":    row.source,
    }


@router.get("/api/prices/{ticker}", response_model=None)
def get_prices(ticker: str, days: int = 30, db: Session = Depends(get_db)):
    if ticker not in TICKER_LIST:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker!r} not found")

    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(RawPrice)
        .filter(RawPrice.ticker == ticker, RawPrice.timestamp >= since)
        .order_by(RawPrice.timestamp.asc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No price data for {ticker!r} in the last {days} days")

    return [
        {
            "ticker":    r.ticker,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "open":      r.open,
            "high":      r.high,
            "low":       r.low,
            "close":     r.close,
            "volume":    r.volume,
            "interval":  r.interval,
            "source":    r.source,
        }
        for r in rows
    ]
