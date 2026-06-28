"""
Stocker — Decision Pydantic Schema
Output model for the Decision Engine.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class Decision(BaseModel):
    id: int
    ticker: str
    action: str
    confidence: int
    composite_score: int
    technical_score: int
    sentiment_score: int
    fundamental_score: int
    target_price: Optional[float]
    stop_loss: float
    time_horizon: str
    reason: str
    risk_approved: bool
    risk_reason: Optional[str]
    ollama_raw: Optional[str]
    decided_at: datetime
    ticker_price: float

    @field_validator("action")
    @classmethod
    def action_valid(cls, v):
        if v not in ("BUY", "SELL", "HOLD"):
            raise ValueError("action must be one of BUY, SELL, HOLD")
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("confidence must be between 0 and 100")
        return v

    @field_validator("composite_score")
    @classmethod
    def composite_in_range(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("composite_score must be between 0 and 100")
        return v

    @field_validator("reason")
    @classmethod
    def reason_min_length(cls, v):
        if len(v) < 20:
            raise ValueError("reason must be at least 20 characters")
        return v
