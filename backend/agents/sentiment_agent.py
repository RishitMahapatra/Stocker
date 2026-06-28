"""
Stocker — Sentiment Analysis Agent
Scores a ticker 0–100 using time-decay-weighted VADER sentiment from raw_news.
"""

import json
import math
import uuid
from datetime import datetime

from backend.database import RawNews, RawPrice, AgentOutput as AgentOutputModel
from backend.schemas.agent import AgentOutput as AgentOutputSchema
from backend.config import (
    SENTIMENT_DECAY_RATE,
    SENTIMENT_CONFIDENCE_BANDS,
    SENTIMENT_MIN_HEADLINES,
    SIGNAL_BUY_THRESHOLD,
    SIGNAL_SELL_THRESHOLD,
)

MODEL_VERSION = "sentiment-v1.0"
AGENT_NAME = "sentiment"


def _get_confidence(count: int) -> int:
    for lo, hi, conf in SENTIMENT_CONFIDENCE_BANDS:
        if lo <= count < hi:
            return conf
    return 0


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
        print(f"[sentiment_agent] Failed to save HOLD fallback: {db_err}")

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
    Run sentiment analysis for ticker and return an AgentOutput schema object.
    Saves result to agent_outputs table.
    """
    try:
        print(f"[sentiment_agent] Starting analysis for {ticker}")

        # Step 1 — Fetch headlines
        headlines = (
            db_session.query(RawNews)
            .filter(RawNews.ticker == ticker)
            .order_by(RawNews.published_at.desc())
            .limit(50)
            .all()
        )

        print(f"[sentiment_agent] Found {len(headlines)} headlines for {ticker}")

        if not headlines:
            return _make_hold_output(
                ticker, db_session,
                reason="No news headlines available for sentiment analysis",
            )

        # Step 2 — Time-decay weighting
        now = datetime.utcnow()
        weighted_sum = 0.0
        weight_total = 0.0
        hours_list = []
        raw_vader_scores = []

        for h in headlines:
            vader = h.vader_score if h.vader_score is not None else 0.0
            pub = h.published_at if h.published_at is not None else now
            hours_old = (now - pub).total_seconds() / 3600.0
            weight = math.exp(-SENTIMENT_DECAY_RATE * hours_old)
            weighted_sum += vader * weight
            weight_total += weight
            hours_list.append(hours_old)
            raw_vader_scores.append(vader)

        weighted_score = weighted_sum / weight_total if weight_total > 0 else 0.0
        print(f"[sentiment_agent] Weighted sentiment score: {weighted_score:.4f}")

        # Step 3 — Convert to 0–100 scale
        raw_score = int((weighted_score + 1.0) / 2.0 * 100)
        raw_score = max(0, min(100, raw_score))

        # Step 4 — Confidence from headline count
        count = len(headlines)
        confidence = _get_confidence(count)

        # Step 5 — Signal
        if raw_score >= SIGNAL_BUY_THRESHOLD:
            signal = "BUY"
        elif raw_score <= SIGNAL_SELL_THRESHOLD:
            signal = "SELL"
        else:
            signal = "HOLD"

        print(f"[sentiment_agent] Score={raw_score}, Signal={signal}, Confidence={confidence}")

        # Step 6 — Reason
        oldest_h  = round(max(hours_list), 1)
        newest_h  = round(min(hours_list), 1)
        reason = (
            f"Sentiment analysis of {count} headlines: "
            f"weighted score={weighted_score:.3f}, "
            f"spanning {newest_h}h–{oldest_h}h ago. "
            f"Signal={signal}."
        )

        # Step 7 — Data snapshot
        avg_raw_vader = sum(raw_vader_scores) / len(raw_vader_scores) if raw_vader_scores else 0.0
        data_snapshot = json.dumps({
            "headlines_count":       count,
            "weighted_score":        round(weighted_score, 6),
            "oldest_headline_hours": oldest_h,
            "newest_headline_hours": newest_h,
            "avg_raw_vader":         round(avg_raw_vader, 6),
            "confidence_band":       confidence,
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
        now_ts = datetime.utcnow()

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
            created_at=now_ts,
            ticker_price=ticker_price,
        )
        db_session.add(db_row)
        db_session.commit()
        print(f"[sentiment_agent] Saved AgentOutput id={output_id} for {ticker}")

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
            created_at=now_ts,
            ticker_price=ticker_price,
        )

    except Exception as e:
        print(f"[sentiment_agent] Unhandled error for {ticker}: {e}")
        return _make_hold_output(
            ticker, db_session,
            reason=f"Sentiment analysis failed: {str(e)[:60]}",
        )
