"""
Stocker — Decision Engine
Aggregates all three agent scores, calls Ollama for a final recommendation,
and falls back to rule-based logic if Ollama is unavailable.
"""

import json
import re
from datetime import datetime, timedelta

import httpx

from backend.database import AgentOutput as AgentOutputModel, Decision as DecisionModel, RawPrice
from backend.schemas.decision import Decision as DecisionSchema
from backend.config import (
    AGENT_WEIGHTS,
    OLLAMA_URL,
    OLLAMA_MODEL,
    FALLBACK_BUY_THRESHOLD,
    FALLBACK_SELL_THRESHOLD,
)


def _fetch_agent_score(ticker: str, agent_name: str, db_session) -> tuple[int, int]:
    """
    Return (score, confidence) for the latest agent output.
    Falls back to (50, 0) if missing or stale (older than 60 min).
    """
    cutoff = datetime.utcnow() - timedelta(minutes=60)
    row = (
        db_session.query(AgentOutputModel)
        .filter(
            AgentOutputModel.ticker == ticker,
            AgentOutputModel.agent_name == agent_name,
        )
        .order_by(AgentOutputModel.created_at.desc())
        .first()
    )
    if row is None or row.created_at < cutoff:
        print(f"[decision_engine] {agent_name} output missing/stale for {ticker} — using 50/0")
        return 50, 0
    return row.score, row.confidence


def _build_prompt(ticker, price, tech_score, tech_conf, sent_score, sent_conf,
                  fund_score, fund_conf, composite_score) -> str:
    return f"""You are a senior investment analyst for Indian stock markets.

Analyze this stock and provide a recommendation:
Ticker: {ticker}
Current Price: ₹{price}

Agent Scores (0-100, higher is more bullish):
- Technical Analysis: {tech_score}/100 (confidence: {tech_conf}%)
- Sentiment Analysis: {sent_score}/100 (confidence: {sent_conf}%)
- Fundamental Analysis: {fund_score}/100 (confidence: {fund_conf}%)
- Composite Score: {composite_score}/100

Respond with ONLY a valid JSON object, no other text:
{{
  "action": "BUY" or "SELL" or "HOLD",
  "confidence": <integer 0-100>,
  "target_price": <float or null>,
  "stop_loss": <float>,
  "time_horizon": "short" or "medium" or "long",
  "reason": "<minimum 20 character explanation>"
}}"""


def _call_ollama(prompt: str) -> dict | None:
    """POST prompt to Ollama and parse JSON from response. Returns None on any failure."""
    try:
        print(f"[decision_engine] Calling Ollama at {OLLAMA_URL} ...")
        resp = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=30.0,
        )
        resp.raise_for_status()
        raw_text = resp.json().get("response", "")

        # Extract first JSON object from the response
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            print("[decision_engine] Ollama response contained no JSON object")
            return None
        parsed = json.loads(match.group())
        print(f"[decision_engine] Ollama response parsed: action={parsed.get('action')}")
        return parsed
    except Exception as e:
        print(f"[decision_engine] Ollama call failed: {e}")
        return None


def decide(ticker: str, db_session) -> DecisionSchema:
    """
    Aggregate agent scores, call Ollama, apply fallback, persist and return Decision.
    """
    try:
        print(f"[decision_engine] Starting decision for {ticker}")

        # Step 1 — Fetch latest agent outputs
        tech_score,  tech_conf  = _fetch_agent_score(ticker, "technical",    db_session)
        sent_score,  sent_conf  = _fetch_agent_score(ticker, "sentiment",    db_session)
        fund_score,  fund_conf  = _fetch_agent_score(ticker, "fundamental",  db_session)

        # Step 2 — Composite score
        w = AGENT_WEIGHTS
        composite = int(
            tech_score  * w["technical"]   +
            sent_score  * w["sentiment"]   +
            fund_score  * w["fundamental"]
        )
        composite = max(0, min(100, composite))
        print(f"[decision_engine] Composite score for {ticker}: {composite}")

        # Fetch current price
        price_row = (
            db_session.query(RawPrice)
            .filter(RawPrice.ticker == ticker)
            .order_by(RawPrice.timestamp.desc())
            .first()
        )
        ticker_price = price_row.close if price_row and price_row.close is not None else 0.0

        # Step 3 & 4 — Build prompt and call Ollama
        prompt = _build_prompt(
            ticker, ticker_price,
            tech_score, tech_conf,
            sent_score, sent_conf,
            fund_score, fund_conf,
            composite,
        )
        ollama_result = _call_ollama(prompt)
        ollama_raw = json.dumps(ollama_result) if ollama_result else None

        # Step 5 — Use Ollama result or fallback
        if ollama_result:
            action       = ollama_result.get("action", "HOLD")
            confidence   = int(ollama_result.get("confidence", 50))
            target_price = ollama_result.get("target_price")
            stop_loss    = float(ollama_result.get("stop_loss") or ticker_price * 0.95)
            time_horizon = ollama_result.get("time_horizon", "medium")
            reason       = ollama_result.get("reason", "Ollama recommendation.")

            if action not in ("BUY", "SELL", "HOLD"):
                action = "HOLD"
            confidence = max(0, min(100, confidence))
            if len(reason) < 20:
                reason = reason.ljust(20)
        else:
            print(f"[decision_engine] Using rule-based fallback for {ticker}")
            if composite >= FALLBACK_BUY_THRESHOLD:
                action = "BUY"
            elif composite <= FALLBACK_SELL_THRESHOLD:
                action = "SELL"
            else:
                action = "HOLD"
            confidence   = 50
            target_price = None
            stop_loss    = ticker_price * 0.95 if ticker_price > 0 else 0.0
            time_horizon = "medium"
            reason       = f"Rule-based fallback: composite score {composite}/100"

        # Step 6 — Persist to decisions table
        now = datetime.utcnow()
        db_row = DecisionModel(
            ticker=ticker,
            action=action,
            confidence=confidence,
            composite_score=composite,
            technical_score=tech_score,
            sentiment_score=sent_score,
            fundamental_score=fund_score,
            target_price=target_price,
            stop_loss=stop_loss,
            time_horizon=time_horizon,
            reason=reason,
            risk_approved=False,
            risk_reason=None,
            ollama_raw=ollama_raw,
            decided_at=now,
            ticker_price=ticker_price,
        )
        db_session.add(db_row)
        db_session.commit()
        db_session.refresh(db_row)
        print(f"[decision_engine] Decision saved id={db_row.id}, action={action}")

        return DecisionSchema(
            id=db_row.id,
            ticker=ticker,
            action=action,
            confidence=confidence,
            composite_score=composite,
            technical_score=tech_score,
            sentiment_score=sent_score,
            fundamental_score=fund_score,
            target_price=target_price,
            stop_loss=stop_loss,
            time_horizon=time_horizon,
            reason=reason,
            risk_approved=False,
            risk_reason=None,
            ollama_raw=ollama_raw,
            decided_at=now,
            ticker_price=ticker_price,
        )

    except Exception as e:
        print(f"[decision_engine] Unhandled error for {ticker}: {e}")
        # Safe fallback — still try to persist
        try:
            now = datetime.utcnow()
            db_row = DecisionModel(
                ticker=ticker,
                action="HOLD",
                confidence=0,
                composite_score=50,
                technical_score=50,
                sentiment_score=50,
                fundamental_score=50,
                target_price=None,
                stop_loss=0.0,
                time_horizon="medium",
                reason=f"Decision engine error: {str(e)[:60]}",
                risk_approved=False,
                risk_reason=str(e)[:200],
                ollama_raw=None,
                decided_at=now,
                ticker_price=0.0,
            )
            db_session.add(db_row)
            db_session.commit()
            db_session.refresh(db_row)
            return DecisionSchema(
                id=db_row.id,
                ticker=ticker,
                action="HOLD",
                confidence=0,
                composite_score=50,
                technical_score=50,
                sentiment_score=50,
                fundamental_score=50,
                target_price=None,
                stop_loss=0.0,
                time_horizon="medium",
                reason=f"Decision engine error: {str(e)[:60]}",
                risk_approved=False,
                risk_reason=str(e)[:200],
                ollama_raw=None,
                decided_at=now,
                ticker_price=0.0,
            )
        except Exception as inner:
            print(f"[decision_engine] Could not persist fallback decision: {inner}")
            raise
