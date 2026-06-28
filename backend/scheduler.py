"""
Stocker — APScheduler Pipeline Scheduler
Runs the full analysis pipeline on a recurring interval during market hours.
"""

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.config import (
    TICKER_LIST,
    SCHEDULE_INTERVAL_MINUTES,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MIN,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MIN,
)
from backend.database import SessionLocal

_IST = ZoneInfo("Asia/Kolkata")


def _is_market_open() -> bool:
    """Return True if current IST time is within market hours on a weekday."""
    now_ist = datetime.now(_IST)
    if now_ist.weekday() >= 5:   # Saturday=5, Sunday=6
        return False
    open_minutes  = MARKET_OPEN_HOUR  * 60 + MARKET_OPEN_MIN
    close_minutes = MARKET_CLOSE_HOUR * 60 + MARKET_CLOSE_MIN
    current_min   = now_ist.hour * 60 + now_ist.minute
    return open_minutes <= current_min <= close_minutes


async def _fetch_and_store_ticker(ticker: str, db) -> None:
    """
    Fetch latest OHLCV data for ticker and store in raw_prices.
    Uses yfinance in a thread executor to avoid blocking the event loop.
    """
    try:
        import yfinance as yf
        from backend.database import RawPrice
        from datetime import timedelta

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: yf.download(ticker, period="5d", interval="1d",
                                 progress=False, auto_adjust=True),
        )
        if data is None or data.empty:
            print(f"[scheduler] No data returned for {ticker}")
            return

        for ts, row in data.iterrows():
            exists = db.query(RawPrice).filter(
                RawPrice.ticker == ticker,
                RawPrice.timestamp == ts.to_pydatetime(),
            ).first()
            if exists:
                continue
            db.add(RawPrice(
                ticker=ticker,
                timestamp=ts.to_pydatetime(),
                open=float(row.get("Open",  0) or 0),
                high=float(row.get("High",  0) or 0),
                low=float(row.get("Low",   0) or 0),
                close=float(row.get("Close", 0) or 0),
                volume=int(row.get("Volume", 0) or 0),
                interval="1d",
                source="yfinance",
            ))
        db.commit()
        print(f"[scheduler] Fetched/updated prices for {ticker}")
    except Exception as e:
        print(f"[scheduler] _fetch_and_store_ticker error for {ticker}: {e}")


async def run_full_pipeline() -> None:
    """
    Run the complete analysis pipeline for all tickers.
    Skips if outside market hours.
    """
    if not _is_market_open():
        print(f"[scheduler] Outside market hours, skipping pipeline run")
        return

    started = datetime.utcnow()
    print(f"[scheduler] Pipeline started at {started.isoformat()} UTC")

    from backend.agents import technical_agent, sentiment_agent, fundamental_agent
    from backend.agents.decision_engine import decide
    from backend.agents.risk_engine import validate

    errors = 0
    for ticker in TICKER_LIST:
        db = SessionLocal()
        try:
            print(f"[scheduler] Processing {ticker} ...")

            await _fetch_and_store_ticker(ticker, db)

            loop = asyncio.get_event_loop()

            await loop.run_in_executor(None, technical_agent.analyze,   ticker, db)
            await loop.run_in_executor(None, sentiment_agent.analyze,   ticker, db)
            await loop.run_in_executor(None, fundamental_agent.analyze, ticker, db)

            decision = await loop.run_in_executor(None, decide, ticker, db)
            await loop.run_in_executor(None, validate, decision, db)

            print(f"[scheduler] Completed {ticker}")
        except Exception as e:
            errors += 1
            print(f"[scheduler] ERROR processing {ticker}: {e}")
        finally:
            db.close()

    elapsed = (datetime.utcnow() - started).total_seconds()
    print(f"[scheduler] Pipeline finished in {elapsed:.1f}s — errors: {errors}")


def start_scheduler() -> AsyncIOScheduler:
    """Create, configure, and start the APScheduler instance."""
    scheduler = AsyncIOScheduler(timezone=_IST)
    scheduler.add_job(
        run_full_pipeline,
        trigger="interval",
        minutes=SCHEDULE_INTERVAL_MINUTES,
        id="full_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    print(f"[scheduler] Started — interval={SCHEDULE_INTERVAL_MINUTES}min, "
          f"market hours {MARKET_OPEN_HOUR}:{MARKET_OPEN_MIN:02d}–"
          f"{MARKET_CLOSE_HOUR}:{MARKET_CLOSE_MIN:02d} IST")
    return scheduler


def stop_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Shut down the scheduler gracefully."""
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        print("[scheduler] Stopped")
