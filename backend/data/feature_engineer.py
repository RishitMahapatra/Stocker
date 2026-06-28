"""
Stocker — Feature Engineer
Computes technical indicators from raw_prices and saves to features table.
"""

import math
import json
from datetime import datetime

import numpy as np
import pandas as pd
import pandas_ta as ta

from backend.database import RawPrice, Feature
from backend.config import MIN_CANDLES_REQUIRED


def _nan_to_none(val):
    """Convert NaN/inf float to None."""
    try:
        if val is None:
            return None
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def compute_features(ticker: str, db_session) -> dict:
    """
    Read last 200 rows from raw_prices for ticker, compute technical indicators,
    save to features table, and return a feature dict.
    """
    try:
        print(f"[feature_engineer] Computing features for {ticker}")

        rows = (
            db_session.query(RawPrice)
            .filter(RawPrice.ticker == ticker)
            .order_by(RawPrice.timestamp.asc())
            .limit(200)
            .all()
        )

        print(f"[feature_engineer] Loaded {len(rows)} rows from raw_prices")

        if len(rows) < 50:
            raise ValueError(f"Insufficient data for ticker: {ticker} (got {len(rows)} rows, need 50)")

        df = pd.DataFrame([{
            "open":   r.open,
            "high":   r.high,
            "low":    r.low,
            "close":  r.close,
            "volume": float(r.volume) if r.volume is not None else np.nan,
        } for r in rows])

        df = df.astype(float)

        print(f"[feature_engineer] Computing RSI, MACD, EMA, BBands, ATR, ADX ...")

        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.atr(length=14, append=True)
        df.ta.adx(length=14, append=True)

        last = df.iloc[-1]

        def g(col):
            return _nan_to_none(last.get(col))

        current_price = _nan_to_none(last["close"])
        volume_avg_20 = _nan_to_none(df["volume"].tail(20).mean())

        high_52 = _nan_to_none(df["high"].max())
        low_52  = _nan_to_none(df["low"].min())

        price_vs_52h = None
        price_vs_52l = None
        if current_price is not None and high_52 and high_52 != 0:
            price_vs_52h = current_price / high_52
        if current_price is not None and low_52 and low_52 != 0:
            price_vs_52l = current_price / low_52

        features = {
            "rsi_14":          g("RSI_14"),
            "macd_line":       g("MACD_12_26_9"),
            "macd_signal":     g("MACDs_12_26_9"),
            "macd_histogram":  g("MACDh_12_26_9"),
            "ema_20":          g("EMA_20"),
            "ema_50":          g("EMA_50"),
            "ema_200":         g("EMA_200"),
            "bb_upper":        g("BBU_20_2.0"),
            "bb_lower":        g("BBL_20_2.0"),
            "bb_middle":       g("BBM_20_2.0"),
            "atr_14":          g("ATRr_14"),
            "adx_14":          g("ADX_14"),
            "current_price":   current_price,
            "volume_avg_20":   volume_avg_20,
            "price_vs_52h":    price_vs_52h,
            "price_vs_52l":    price_vs_52l,
        }

        print(f"[feature_engineer] Saving features to DB for {ticker}")

        feature_row = Feature(
            ticker=ticker,
            computed_at=datetime.utcnow(),
            rsi_14=features["rsi_14"],
            macd_line=features["macd_line"],
            macd_signal=features["macd_signal"],
            macd_histogram=features["macd_histogram"],
            ema_20=features["ema_20"],
            ema_50=features["ema_50"],
            ema_200=features["ema_200"],
            bb_upper=features["bb_upper"],
            bb_lower=features["bb_lower"],
            bb_middle=features["bb_middle"],
            atr_14=features["atr_14"],
            adx_14=features["adx_14"],
            current_price=features["current_price"],
            volume_avg_20=features["volume_avg_20"],
            price_vs_52h=features["price_vs_52h"],
            price_vs_52l=features["price_vs_52l"],
        )
        db_session.add(feature_row)
        db_session.commit()

        print(f"[feature_engineer] Features computed and saved for {ticker}")
        return features

    except ValueError:
        raise
    except Exception as e:
        print(f"[feature_engineer] ERROR for {ticker}: {e}")
        raise
