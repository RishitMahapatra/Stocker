"""
Stocker — Fundamental Analysis Agent
Scores a ticker 0–100 using weighted fundamental metrics from raw_fundamentals.
"""

import json
import uuid
from datetime import datetime

from backend.database import RawFundamental, RawPrice, AgentOutput as AgentOutputModel
from backend.schemas.agent import AgentOutput as AgentOutputSchema
from backend.config import (
    PE_GOOD_MAX,
    PE_ACCEPTABLE_MAX,
    REVENUE_GROWTH_GOOD,
    PROFIT_MARGIN_GOOD,
    PROFIT_MARGIN_OK,
    DEBT_EQUITY_GOOD_MAX,
    DEBT_EQUITY_OK_MAX,
    ROE_GOOD_MIN,
    ROE_OK_MIN,
    FUNDAMENTAL_METRIC_WEIGHTS,
    SIGNAL_BUY_THRESHOLD,
    SIGNAL_SELL_THRESHOLD,
)

MODEL_VERSION = "fundamental-v1.0"
AGENT_NAME = "fundamental"


def _score_pe(pe) -> int:
    if pe is None:
        return 0
    if pe <= PE_GOOD_MAX:
        return 1
    if pe <= PE_ACCEPTABLE_MAX:
        return 0
    return -1


def _score_revenue(rev) -> int:
    if rev is None:
        return 0
    if rev >= REVENUE_GROWTH_GOOD:
        return 1
    if rev >= 0:
        return 0
    return -1


def _score_margin(margin) -> int:
    if margin is None:
        return 0
    if margin >= PROFIT_MARGIN_GOOD:
        return 1
    if margin >= PROFIT_MARGIN_OK:
        return 0
    return -1


def _score_debt(debt) -> int:
    if debt is None:
        return 0
    if debt <= DEBT_EQUITY_GOOD_MAX:
        return 1
    if debt <= DEBT_EQUITY_OK_MAX:
        return 0
    return -1


def _score_roe(roe) -> int:
    if roe is None:
        return 0
    if roe >= ROE_GOOD_MIN:
        return 1
    if roe >= ROE_OK_MIN:
        return 0
    return -1


def _make_hold_output(ticker: str, db_session, reason: str, ticker_price: float = 0.0) -> AgentOutputSchema:
    if len(reason) < 20:
        reason = reason.ljust(20)

    output_id = str(uuid.uuid4())
    now = datetime.utcnow()

    try:
        db_row = AgentOutputModel(
            id=output_id,
            ticker=ticker,
            agent_name=AGENT_NAME,
            score=50,
            confidence=0,
            signal="HOLD",
            reason=reason,
            data_snapshot="{}",
            model_version=MODEL_VERSION,
            created_at=now,
            ticker_price=ticker_price,
        )
        db_session.add(db_row)
        db_session.commit()
    except Exception as db_err:
        print(f"[fundamental_agent] Failed to save HOLD fallback: {db_err}")

    return AgentOutputSchema(
        id=output_id,
        ticker=ticker,
        agent_name=AGENT_NAME,
        score=50,
        confidence=0,
        signal="HOLD",
        reason=reason,
        data_snapshot="{}",
        model_version=MODEL_VERSION,
        created_at=now,
        ticker_price=ticker_price,
    )


def analyze(ticker: str, db_session) -> AgentOutputSchema:
    """
    Run fundamental analysis for ticker and return an AgentOutput schema object.
    Saves result to agent_outputs table.
    """
    try:
        print(f"[fundamental_agent] Starting analysis for {ticker}")

        # Step 1 — Fetch fundamentals
        row = (
            db_session.query(RawFundamental)
            .filter(RawFundamental.ticker == ticker)
            .order_by(RawFundamental.fetched_at.desc())
            .first()
        )

        if row is None:
            print(f"[fundamental_agent] No fundamental data found for {ticker}")
            return _make_hold_output(
                ticker, db_session,
                reason="No fundamental data available for this ticker",
            )

        pe     = row.pe_ratio
        rev    = row.revenue_growth
        margin = row.profit_margin
        debt   = row.debt_to_equity
        roe    = row.roe

        print(f"[fundamental_agent] Data: PE={pe}, Rev={rev}, Margin={margin}, D/E={debt}, ROE={roe}")

        # Step 2 — Score each metric
        pe_score      = _score_pe(pe)
        revenue_score = _score_revenue(rev)
        margin_score  = _score_margin(margin)
        debt_score    = _score_debt(debt)
        roe_score     = _score_roe(roe)

        # Step 3 — Weighted score
        w = FUNDAMENTAL_METRIC_WEIGHTS
        weighted_sum = (
            pe_score      * w["pe"]      +
            revenue_score * w["revenue"] +
            margin_score  * w["margin"]  +
            debt_score    * w["debt"]    +
            roe_score     * w["roe"]
        )
        raw_score = int((weighted_sum + 1.0) / 2.0 * 100)
        raw_score = max(0, min(100, raw_score))

        # Step 4 — Confidence from non-null metric count
        metrics_available = sum(1 for v in (pe, rev, margin, debt, roe) if v is not None)
        if metrics_available <= 1:
            confidence = 0
        elif metrics_available <= 3:
            confidence = 40
        elif metrics_available == 4:
            confidence = 70
        else:
            confidence = 90

        # Step 5 — Signal
        if raw_score >= SIGNAL_BUY_THRESHOLD:
            signal = "BUY"
        elif raw_score <= SIGNAL_SELL_THRESHOLD:
            signal = "SELL"
        else:
            signal = "HOLD"

        print(f"[fundamental_agent] Score={raw_score}, Signal={signal}, Confidence={confidence}")

        # Step 6 — Reason
        def _fmt(v):
            return f"{v:.2f}" if v is not None else "N/A"

        reason = (
            f"PE={_fmt(pe)}, RevGrowth={_fmt(rev)}, Margin={_fmt(margin)}, "
            f"D/E={_fmt(debt)}, ROE={_fmt(roe)}. "
            f"Signal={signal}."
        )

        # Step 7 — Data snapshot
        data_snapshot = json.dumps({
            "pe_ratio":        pe,
            "revenue_growth":  rev,
            "profit_margin":   margin,
            "debt_to_equity":  debt,
            "roe":             roe,
            "pe_score":        pe_score,
            "revenue_score":   revenue_score,
            "margin_score":    margin_score,
            "debt_score":      debt_score,
            "roe_score":       roe_score,
            "weighted_sum":    round(weighted_sum, 6),
            "metrics_available": metrics_available,
        })

        # Step 8 — Fetch ticker price
        price_row = (
            db_session.query(RawPrice)
            .filter(RawPrice.ticker == ticker)
            .order_by(RawPrice.timestamp.desc())
            .first()
        )
        ticker_price = price_row.close if price_row and price_row.close is not None else 0.0

        output_id = str(uuid.uuid4())
        now = datetime.utcnow()

        db_row = AgentOutputModel(
            id=output_id,
            ticker=ticker,
            agent_name=AGENT_NAME,
            score=raw_score,
            confidence=confidence,
            signal=signal,
            reason=reason,
            data_snapshot=data_snapshot,
            model_version=MODEL_VERSION,
            created_at=now,
            ticker_price=ticker_price,
        )
        db_session.add(db_row)
        db_session.commit()
        print(f"[fundamental_agent] Saved AgentOutput id={output_id} for {ticker}")

        # Step 9 — Return Pydantic object
        return AgentOutputSchema(
            id=output_id,
            ticker=ticker,
            agent_name=AGENT_NAME,
            score=raw_score,
            confidence=confidence,
            signal=signal,
            reason=reason,
            data_snapshot=data_snapshot,
            model_version=MODEL_VERSION,
            created_at=now,
            ticker_price=ticker_price,
        )

    except Exception as e:
        print(f"[fundamental_agent] Unhandled error for {ticker}: {e}")
        return _make_hold_output(
            ticker, db_session,
            reason=f"Fundamental analysis failed: {str(e)[:60]}",
        )
