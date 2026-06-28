"""
Stocker — AgentOutput Pydantic Schema
Shared output model for all agents (technical, sentiment, fundamental).
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, field_validator
import uuid


class AgentOutput(BaseModel):
    id: str
    ticker: str
    agent_name: str
    score: int
    confidence: int
    signal: str
    reason: str
    data_snapshot: str
    model_version: str
    created_at: datetime
    ticker_price: float

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("score must be between 0 and 100")
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v):
        if not (0 <= v <= 100):
            raise ValueError("confidence must be between 0 and 100")
        return v

    @field_validator("signal")
    @classmethod
    def signal_valid(cls, v):
        if v not in ("BUY", "SELL", "HOLD"):
            raise ValueError("signal must be one of BUY, SELL, HOLD")
        return v

    @field_validator("reason")
    @classmethod
    def reason_min_length(cls, v):
        if len(v) < 20:
            raise ValueError("reason must be at least 20 characters")
        return v
