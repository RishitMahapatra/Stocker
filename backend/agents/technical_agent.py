"""
Stocker — Technical Analysis Agent
Scores a ticker 0–100 using RSI, MACD, EMA trend, Bollinger Bands, and ADX.
"""

import json
import uuid
from datetime import datetime

from backend.data.feature_engineer import compute_features
from backend.schemas.agent import AgentOutput as AgentOutputSchema
from backend.database import AgentOutput as AgentOutputModel
from backend.config import SIGNAL_BUY_THRESHOLD, SIGNAL_SELL_THRESHOLD

MODEL_VERSION = "technical-v1.0"
AGENT_NAME = "technical"


def _rsi_vote(rsi) -> int:
    if rsi is None:
        return 0
    if rsi < 30:
        return 1
    if rsi > 70:
        return -1
    return 0


def _macd_vote(macd_line, macd_signal, macd_histogram) -> int:
    if macd_line is None or macd_signal is None or macd_histogram is None:
        return 0
    if macd_line > macd_signal and macd_histogram > 0:
        return 1
    if macd_line < macd_signal and macd_histogram < 0:
        return -1
    return 0


def _ema_vote(price, ema_20, ema_50, ema_200) -> int:
    if any(v is None for v in (price, ema_20, ema_50, ema_200)):
        return 0
    if price > ema_20 > ema_50 > ema_200:
        return 1
    if price < ema_20 < ema_50 < ema_200:
        return -1
    return 0


def _bb_vote(price, bb_upper, bb_lower) -> int:
    if any(v is None for v in (price, bb_upper, bb_lower)):
        return 0
    if price < bb_lower:
        return 1
    if price > bb_upper:
        return -1
    return 0


def _adx_vote(adx, macd_line, macd_signal) -> int:
    if adx is None or macd_line is None or macd_signal is None:
        return 0
    if adx > 25 and macd_line > macd_signal:
        return 1
    if adx > 25 and macd_line < macd_signal:
        return -1
    return 0


def analyze(ticker: str, db_session) -> AgentOutputSchema:
    """
    Run technical analysis for ticker and return an AgentOutput schema object.
    Saves result to agent_outputs table.
    """
    try:
        print(f"[technical_agent] Starting analysis for {ticker}")

        try:
            features = compute_features(ticker, db_session)
        except Exception as fe:
            print(f"[technical_agent] compute_features failed for {ticker}: {fe}")
            return _make_hold_output(ticker, db_session, reason="Insufficient data for technical analysis")

        rsi     = features.get("rsi_14")
        macd_l  = features.get("macd_line")
        macd_s  = features.get("macd_signal")
        macd_h  = features.get("macd_histogram")
        ema_20  = features.get("ema_20")
        ema_50  = features.get("ema_50")
        ema_200 = features.get("ema_200")
        bb_u    = features.get("bb_upper")
        bb_l    = features.get("bb_lower")
        adx     = features.get("adx_14")
        price   = features.get("current_price")

        v_rsi  = _rsi_vote(rsi)
        v_macd = _macd_vote(macd_l, macd_s, macd_h)
        v_ema  = _ema_vote(price, ema_20, ema_50, ema_200)
        v_bb   = _bb_vote(price, bb_u, bb_l)
        v_adx  = _adx_vote(adx, macd_l, macd_s)

        total_votes = v_rsi + v_macd + v_ema + v_bb + v_adx
        print(f"[technical_agent] Votes — RSI:{v_rsi} MACD:{v_macd} EMA:{v_ema} BB:{v_bb} ADX:{v_adx} total:{total_votes}")

        raw_score = int((total_votes + 5) / 10 * 100)
        raw_score = max(0, min(100, raw_score))

        confidence = int(min(adx, 100)) if adx is not None else 50

        if raw_score >= SIGNAL_BUY_THRESHOLD:
            signal = "BUY"
        elif raw_score <= SIGNAL_SELL_THRESHOLD:
            signal = "SELL"
        else:
            signal = "HOLD"

        rsi_str   = f"{rsi:.1f}" if rsi is not None else "N/A"
        macd_dir  = "bullish" if v_macd > 0 else ("bearish" if v_macd < 0 else "neutral")
        ema_trend = "uptrend" if v_ema > 0 else ("downtrend" if v_ema < 0 else "mixed"  )

        reason = (
            f"RSI={rsi_str} ({('oversold' if v_rsi > 0 else 'overbought' if v_rsi < 0 else 'neutral')}), "
            f"MACD is {macd_dir}, EMA trend is {ema_trend}. "
            f"Score={raw_score}, Signal={signal}."
        )

        data_snapshot = json.dumps({k: (v if v is None else round(v, 4) if isinstance(v, float) else v)
                                    for k, v in features.items()})

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
            ticker_price=price if price is not None else 0.0,
        )
        db_session.add(db_row)
        db_session.commit()
        print(f"[technical_agent] Saved AgentOutput id={output_id} for {ticker}")

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
            ticker_price=price if price is not None else 0.0,
        )

    except Exception as e:
        print(f"[technical_agent] Unhandled error for {ticker}: {e}")
        return _make_hold_output(ticker, db_session, reason=f"Technical analysis error: {str(e)[:60]}")


def _make_hold_output(ticker: str, db_session, reason: str) -> AgentOutputSchema:
    """Return a safe HOLD output when analysis cannot proceed."""
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
            ticker_price=0.0,
        )
        db_session.add(db_row)
        db_session.commit()
    except Exception as db_err:
        print(f"[technical_agent] Failed to save HOLD fallback: {db_err}")

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
        ticker_price=0.0,
    )
