"""
Stocker — Database Setup
SQLAlchemy engine, table definitions, and session factory.
All tables defined here match the schemas in the Architecture Bible (Part C).
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, Float, String,
    Boolean, Text, DateTime, BigInteger, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker

# ────────────────────────────────────────
# Engine Setup
# ────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "./data/investment_mvp.db")

# Ensure the data/ directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ────────────────────────────────────────
# Table: raw_prices  (C2 — MarketData)
# ────────────────────────────────────────
class RawPrice(Base):
    __tablename__ = "raw_prices"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    ticker     = Column(String, nullable=False, index=True)
    timestamp  = Column(DateTime, nullable=False)
    open       = Column(Float)
    high       = Column(Float)
    low        = Column(Float)
    close      = Column(Float, nullable=False)
    volume     = Column(BigInteger)
    interval   = Column(String, default="1d")
    source     = Column(String, default="yfinance")
    fetched_at = Column(DateTime, default=datetime.utcnow)


# ────────────────────────────────────────
# Table: raw_news  (C3)
# ────────────────────────────────────────
class RawNews(Base):
    __tablename__ = "raw_news"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    ticker       = Column(String, nullable=False, index=True)
    headline     = Column(Text, nullable=False)
    source       = Column(String)
    url          = Column(String)
    published_at = Column(DateTime)
    vader_score  = Column(Float)
    fetched_at   = Column(DateTime, default=datetime.utcnow)


# ────────────────────────────────────────
# Table: raw_fundamentals  (C4)
# ────────────────────────────────────────
class RawFundamental(Base):
    __tablename__ = "raw_fundamentals"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    ticker         = Column(String, nullable=False, index=True)
    pe_ratio       = Column(Float)
    eps            = Column(Float)
    revenue_growth = Column(Float)
    profit_margin  = Column(Float)
    debt_to_equity = Column(Float)
    roe            = Column(Float)
    price_to_book  = Column(Float)
    market_cap     = Column(BigInteger)
    dividend_yield = Column(Float)
    sector         = Column(String)
    fetched_at     = Column(DateTime, default=datetime.utcnow)


# ────────────────────────────────────────
# Table: features  (C5)
# ────────────────────────────────────────
class Feature(Base):
    __tablename__ = "features"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    ticker        = Column(String, nullable=False, index=True)
    computed_at   = Column(DateTime, default=datetime.utcnow)
    rsi_14        = Column(Float)
    macd_line     = Column(Float)
    macd_signal   = Column(Float)
    macd_histogram= Column(Float)
    ema_20        = Column(Float)
    ema_50        = Column(Float)
    ema_200       = Column(Float)
    bb_upper      = Column(Float)
    bb_lower      = Column(Float)
    bb_middle     = Column(Float)
    atr_14        = Column(Float)
    adx_14        = Column(Float)
    current_price = Column(Float)
    volume_avg_20 = Column(Float)
    price_vs_52h  = Column(Float)
    price_vs_52l  = Column(Float)


# ────────────────────────────────────────
# Table: agent_outputs  (C1 — AgentOutput)
# ────────────────────────────────────────
class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    id            = Column(String, primary_key=True)   # UUID
    ticker        = Column(String, nullable=False, index=True)
    agent_name    = Column(String, nullable=False)      # technical | sentiment | fundamental
    score         = Column(Integer, nullable=False)     # 0–100
    confidence    = Column(Integer, nullable=False)     # 0–100
    signal        = Column(String, nullable=False)      # BUY | SELL | HOLD
    reason        = Column(Text, nullable=False)
    data_snapshot = Column(Text, nullable=False)        # JSON string
    model_version = Column(String, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    ticker_price  = Column(Float, nullable=False)


# ────────────────────────────────────────
# Table: decisions  (C6)
# ────────────────────────────────────────
class Decision(Base):
    __tablename__ = "decisions"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    ticker            = Column(String, nullable=False, index=True)
    action            = Column(String, nullable=False)   # BUY | SELL | HOLD
    confidence        = Column(Integer)
    composite_score   = Column(Integer)
    technical_score   = Column(Integer)
    sentiment_score   = Column(Integer)
    fundamental_score = Column(Integer)
    target_price      = Column(Float, nullable=True)
    stop_loss         = Column(Float)
    time_horizon      = Column(String)                   # short | medium | long
    reason            = Column(Text)
    risk_approved     = Column(Boolean, default=False)
    risk_reason       = Column(Text, nullable=True)
    ollama_raw        = Column(Text, nullable=True)
    decided_at        = Column(DateTime, default=datetime.utcnow)
    ticker_price      = Column(Float)


# ────────────────────────────────────────
# Table: paper_trades  (C7)
# ────────────────────────────────────────
class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    decision_id     = Column(Integer, ForeignKey("decisions.id"))
    ticker          = Column(String, nullable=False, index=True)
    action          = Column(String, nullable=False)     # BUY | SELL
    quantity        = Column(Integer)
    entry_price     = Column(Float)
    stop_loss_price = Column(Float)
    target_price    = Column(Float, nullable=True)
    status          = Column(String, default="OPEN")     # OPEN | CLOSED | STOPPED
    exit_price      = Column(Float, nullable=True)
    exit_reason     = Column(String, nullable=True)      # TARGET | STOP_LOSS | MANUAL
    pnl             = Column(Float, nullable=True)
    pnl_pct         = Column(Float, nullable=True)
    entered_at      = Column(DateTime, default=datetime.utcnow)
    exited_at       = Column(DateTime, nullable=True)


# ────────────────────────────────────────
# Table: pipeline_runs  (Phase 9)
# ────────────────────────────────────────
class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    run_id              = Column(String, nullable=False)
    started_at          = Column(DateTime, default=datetime.utcnow)
    completed_at        = Column(DateTime, nullable=True)
    tickers_processed   = Column(Integer, default=0)
    errors              = Column(Integer, default=0)
    duration_seconds    = Column(Float, nullable=True)


# ────────────────────────────────────────
# Create All Tables
# ────────────────────────────────────────
def create_all_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully.")
    print(f"   Database: {DB_PATH}")


# ────────────────────────────────────────
# Session Factory
# ────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ────────────────────────────────────────
# Run directly to initialise DB
# ────────────────────────────────────────
if __name__ == "__main__":
    create_all_tables()

    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Tables in database ({len(tables)} total):")
    for t in tables:
        print(f"   - {t}")