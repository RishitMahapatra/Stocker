"""
Stocker — Feature Engineer
Computes technical indicators from raw_prices and saves to features table.

NOTE: Uses TA-Lib (ta-lib package) since pandas-ta is not available for
Python 3.11 on PyPI. Column name conventions follow the pandas-ta naming
scheme as documented in the Architecture Bible so downstream code is
unaffected.
"""

import math
import json
from datetime import datetime

import numpy as np
import pandas as pd
import talib

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
    Read last 200 rows from raw_prices for ticker, compute technical indicators
    via TA-Lib, save to features table, and return a feature dict.
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

        close  = df["close"].values.astype(np.float64)
        high   = df["high"].values.astype(np.float64)
        low    = df["low"].values.astype(np.float64)
        volume = df["volume"].values.astype(np.float64)

        print(f"[feature_engineer] Computing RSI, MACD, EMA, BBands, ATR, ADX ...")

        # RSI_14
        rsi_arr = talib.RSI(close, timeperiod=14)

        # MACD_12_26_9
        macd_arr, macds_arr, macdh_arr = talib.MACD(
            close, fastperiod=12, slowperiod=26, signalperiod=9
        )

        # EMA_20, EMA_50, EMA_200
        ema20_arr  = talib.EMA(close, timeperiod=20)
        ema50_arr  = talib.EMA(close, timeperiod=50)
        ema200_arr = talib.EMA(close, timeperiod=200)

        # BBands (20, 2.0)
        bbu_arr, bbm_arr, bbl_arr = talib.BBANDS(
            close, timeperiod=20, nbdevup=2.0, nbdevdn=2.0, matype=0
        )

        # ATR_14
        atr_arr = talib.ATR(high, low, close, timeperiod=14)

        # ADX_14
        adx_arr = talib.ADX(high, low, close, timeperiod=14)

        def last(arr):
            return _nan_to_none(arr[-1])

        current_price = _nan_to_none(close[-1])
        volume_avg_20 = _nan_to_none(np.nanmean(volume[-20:]))

        high_52 = _nan_to_none(np.nanmax(high))
        low_52  = _nan_to_none(np.nanmin(low))

        price_vs_52h = None
        price_vs_52l = None
        if current_price is not None and high_52 and high_52 != 0:
            price_vs_52h = current_price / high_52
        if current_price is not None and low_52 and low_52 != 0:
            price_vs_52l = current_price / low_52

        features = {
            "rsi_14":          last(rsi_arr),
            "macd_line":       last(macd_arr),
            "macd_signal":     last(macds_arr),
            "macd_histogram":  last(macdh_arr),
            "ema_20":          last(ema20_arr),
            "ema_50":          last(ema50_arr),
            "ema_200":         last(ema200_arr),
            "bb_upper":        last(bbu_arr),
            "bb_lower":        last(bbl_arr),
            "bb_middle":       last(bbm_arr),
            "atr_14":          last(atr_arr),
            "adx_14":          last(adx_arr),
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
