"""
Stocker — Signal Routes
/api/signals, /api/signals/{ticker}, /api/signals/{ticker}/history,
/api/agent-outputs/{ticker}
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.config import TICKER_LIST
from backend.database import get_db, Decision as DecisionModel, AgentOutput as AgentOutputModel

router = APIRouter()

_AGENTS = ["technical", "sentiment", "fundamental"]


def _decision_to_dict(d) -> dict:
    return {
        "id":                d.id,
        "ticker":            d.ticker,
        "action":            d.action,
        "confidence":        d.confidence,
        "composite_score":   d.composite_score,
        "technical_score":   d.technical_score,
        "sentiment_score":   d.sentiment_score,
        "fundamental_score": d.fundamental_score,
        "target_price":      d.target_price,
        "stop_loss":         d.stop_loss,
        "time_horizon":      d.time_horizon,
        "reason":            d.reason,
        "risk_approved":     d.risk_approved,
        "risk_reason":       d.risk_reason,
        "ollama_raw":        d.ollama_raw,
        "decided_at":        d.decided_at.isoformat() if d.decided_at else None,
        "ticker_price":      d.ticker_price,
    }


def _agent_output_to_dict(a) -> dict:
    return {
        "id":            a.id,
        "ticker":        a.ticker,
        "agent_name":    a.agent_name,
        "score":         a.score,
        "confidence":    a.confidence,
        "signal":        a.signal,
        "reason":        a.reason,
        "data_snapshot": a.data_snapshot,
        "model_version": a.model_version,
        "created_at":    a.created_at.isoformat() if a.created_at else None,
        "ticker_price":  a.ticker_price,
    }


def _latest_decision(ticker: str, db: Session):
    return (
        db.query(DecisionModel)
        .filter(DecisionModel.ticker == ticker)
        .order_by(DecisionModel.decided_at.desc())
        .first()
    )


def _latest_agent_output(ticker: str, agent_name: str, db: Session):
    return (
        db.query(AgentOutputModel)
        .filter(AgentOutputModel.ticker == ticker,
                AgentOutputModel.agent_name == agent_name)
        .order_by(AgentOutputModel.created_at.desc())
        .first()
    )


@router.get("/api/signals", response_model=None)
def get_all_signals(db: Session = Depends(get_db)):
    results = []
    for ticker in TICKER_LIST:
        d = _latest_decision(ticker, db)
        if d is None:
            continue
        results.append({
            "ticker":            d.ticker,
            "action":            d.action,
            "composite_score":   d.composite_score,
            "confidence":        d.confidence,
            "technical_score":   d.technical_score,
            "sentiment_score":   d.sentiment_score,
            "fundamental_score": d.fundamental_score,
            "decided_at":        d.decided_at.isoformat() if d.decided_at else None,
            "risk_approved":     d.risk_approved,
            "ticker_price":      d.ticker_price,
        })
    return results


@router.get("/api/signals/{ticker}", response_model=None)
def get_ticker_signal(ticker: str, db: Session = Depends(get_db)):
    if ticker not in TICKER_LIST:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker!r} not found")

    d = _latest_decision(ticker, db)
    if d is None:
        raise HTTPException(status_code=404, detail=f"No decision found for {ticker!r}")

    agent_outputs = {
        agent: _agent_output_to_dict(row) if (row := _latest_agent_output(ticker, agent, db)) else None
        for agent in _AGENTS
    }

    return {
        "decision": _decision_to_dict(d),
        "agents":   agent_outputs,
    }


@router.get("/api/signals/{ticker}/history", response_model=None)
def get_ticker_signal_history(ticker: str, limit: int = 20, db: Session = Depends(get_db)):
    if ticker not in TICKER_LIST:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker!r} not found")

    rows = (
        db.query(DecisionModel)
        .filter(DecisionModel.ticker == ticker)
        .order_by(DecisionModel.decided_at.desc())
        .limit(limit)
        .all()
    )
    return [_decision_to_dict(r) for r in rows]


@router.get("/api/agent-outputs/{ticker}", response_model=None)
def get_agent_outputs(ticker: str, db: Session = Depends(get_db)):
    if ticker not in TICKER_LIST:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker!r} not found")

    return {
        agent: _agent_output_to_dict(row) if (row := _latest_agent_output(ticker, agent, db)) else None
        for agent in _AGENTS
    }
