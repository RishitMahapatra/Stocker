"""
Stocker — Data Fetcher
Utilities for fetching current market prices.
"""

from typing import Optional


def fetch_current_price(ticker: str) -> Optional[float]:
    """
    Fetch the latest price for a ticker via yfinance.
    Returns None on any failure so callers can skip gracefully.
    """
    try:
        import yfinance as yf
        data = yf.download(ticker, period="1d", interval="1m",
                           progress=False, auto_adjust=True)
        if data is None or data.empty:
            print(f"[fetcher] No price data returned for {ticker}")
            return None
        price = float(data["Close"].iloc[-1])
        print(f"[fetcher] Current price for {ticker}: {price}")
        return price
    except Exception as e:
        print(f"[fetcher] fetch_current_price error for {ticker}: {e}")
        return None
