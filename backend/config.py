"""
Stocker — Central Configuration
All constants, thresholds, and settings live here.
Never hardcode values in agent files — always import from config.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────
# Tickers
# ────────────────────────────────────────
TICKER_LIST = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "WIPRO.NS",
    "BAJFINANCE.NS",
    "AXISBANK.NS",
    "MARUTI.NS",
    "TATAMOTORS.NS",
]

# ────────────────────────────────────────
# Ollama (Local LLM)
# ────────────────────────────────────────
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# ────────────────────────────────────────
# Database
# ────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "./data/investment_mvp.db")

# ────────────────────────────────────────
# Scheduler
# ────────────────────────────────────────
SCHEDULE_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", 15))

# Market hours IST (24h format)
MARKET_OPEN_HOUR   = 9
MARKET_OPEN_MIN    = 15
MARKET_CLOSE_HOUR  = 15
MARKET_CLOSE_MIN   = 30

# ────────────────────────────────────────
# Paper Trading
# ────────────────────────────────────────
PAPER_CAPITAL            = float(os.getenv("PAPER_CAPITAL", 1_000_000))  # ₹10 lakh
MAX_POSITION_PCT         = 0.10   # Max 10% of capital per position
MAX_SECTOR_PCT           = 0.30   # Max 30% of capital per sector
STOP_LOSS_ATR_MULTIPLIER = 2.0    # Stop loss = entry - (ATR × 2)
MAX_DRAWDOWN_LIMIT       = 0.15   # No new BUYs if portfolio down > 15%

# ────────────────────────────────────────
# Agent Weights (must sum to 1.0)
# ────────────────────────────────────────
AGENT_WEIGHTS = {
    "technical":   0.35,
    "sentiment":   0.25,
    "fundamental": 0.40,
}

# ────────────────────────────────────────
# Signal Thresholds
# ────────────────────────────────────────
SIGNAL_BUY_THRESHOLD  = 60   # Score >= 60 → BUY
SIGNAL_SELL_THRESHOLD = 40   # Score <= 40 → SELL
                              # 40 < score < 60 → HOLD

# Decision engine fallback (when Ollama is unavailable)
FALLBACK_BUY_THRESHOLD  = 65
FALLBACK_SELL_THRESHOLD = 35

# ────────────────────────────────────────
# Fundamental Scoring Thresholds
# ────────────────────────────────────────
PE_GOOD_MAX           = 25     # PE below this → bullish
PE_ACCEPTABLE_MAX     = 40     # PE below this → neutral; above → bearish
REVENUE_GROWTH_GOOD   = 0.15   # 15%+ YoY growth → bullish
PROFIT_MARGIN_GOOD    = 0.15   # 15%+ margin → bullish
PROFIT_MARGIN_OK      = 0.05   # 5–15% margin → neutral
DEBT_EQUITY_GOOD_MAX  = 0.5    # D/E below 0.5 → bullish
DEBT_EQUITY_OK_MAX    = 1.0    # D/E below 1.0 → neutral; above → bearish
ROE_GOOD_MIN          = 0.15   # ROE above 15% → bullish
ROE_OK_MIN            = 0.08   # ROE above 8% → neutral; below → bearish
PRICE_BOOK_GOOD_MAX   = 3.0    # P/B below 3 → bullish

# Fundamental metric weights (must sum to 1.0)
FUNDAMENTAL_METRIC_WEIGHTS = {
    "pe":      0.25,
    "revenue": 0.20,
    "margin":  0.20,
    "debt":    0.20,
    "roe":     0.15,
}

# ────────────────────────────────────────
# Sentiment Scoring
# ────────────────────────────────────────
SENTIMENT_DECAY_RATE        = 0.1   # Exponential decay per hour
SENTIMENT_MIN_HEADLINES     = 3     # Minimum headlines needed for analysis
SENTIMENT_CONFIDENCE_BANDS  = [
    (0,  3,  0),    # < 3 headlines  → confidence 0
    (3,  10, 30),   # 3–9 headlines  → confidence 30
    (10, 20, 60),   # 10–19 headlines → confidence 60
    (20, float("inf"), 90),  # 20+ headlines → confidence 90
]

# ────────────────────────────────────────
# RSS Feed Sources
# ────────────────────────────────────────
RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "https://news.google.com/rss/search?q={ticker}+NSE+stock&hl=en-IN&gl=IN&ceid=IN:en",
]

# ────────────────────────────────────────
# Data Fetching
# ────────────────────────────────────────
OHLCV_PERIOD        = "1y"    # Fetch 1 year of daily data
OHLCV_INTERVAL      = "1d"    # Daily candles
MIN_CANDLES_REQUIRED = 200    # Minimum rows needed for technical analysis
FETCH_SLEEP_SECONDS  = 0.5    # Sleep between ticker fetches to avoid rate limits
MAX_NEWS_PER_TICKER  = 50     # Max headlines stored per ticker per fetch

# ────────────────────────────────────────
# App
# ────────────────────────────────────────
APP_HOST     = os.getenv("APP_HOST", "localhost")
APP_PORT     = int(os.getenv("APP_PORT", 8000))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")