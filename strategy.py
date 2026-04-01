"""Trading strategy: EMA 9/21 crossover + RSI + ATR SL/TP + ADX filter + 200 EMA trend."""

import pandas as pd
import numpy as np

from config import (
    EMA_FAST, EMA_SLOW, EMA_TREND,
    RSI_PERIOD, RSI_LONG_MIN, RSI_SHORT_MAX,
    ATR_PERIOD, ATR_SL_MULT, ATR_TP_MULT,
    ADX_PERIOD, ADX_MIN,
)


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # EMAs
    df["ema_fast"] = df["close"].ewm(span=EMA_FAST, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=EMA_SLOW, adjust=False).mean()
    df["ema_trend"] = df["close"].ewm(span=EMA_TREND, adjust=False).mean()

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=RSI_PERIOD - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=RSI_PERIOD - 1, adjust=False).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # ATR
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    df["atr"] = pd.concat([hl, hc, lc], axis=1).max(axis=1).ewm(span=ATR_PERIOD, adjust=False).mean()

    # ADX
    df["dm_plus"] = np.where(
        (df["high"] - df["high"].shift()) > (df["low"].shift() - df["low"]),
        (df["high"] - df["high"].shift()).clip(lower=0), 0
    )
    df["dm_minus"] = np.where(
        (df["low"].shift() - df["low"]) > (df["high"] - df["high"].shift()),
        (df["low"].shift() - df["low"]).clip(lower=0), 0
    )
    atr_adx = pd.concat([hl, hc, lc], axis=1).max(axis=1).ewm(span=ADX_PERIOD, adjust=False).mean()
    di_plus = 100 * df["dm_plus"].ewm(span=ADX_PERIOD, adjust=False).mean() / atr_adx
    di_minus = 100 * df["dm_minus"].ewm(span=ADX_PERIOD, adjust=False).mean() / atr_adx
    dx = (100 * (di_plus - di_minus).abs() / (di_plus + di_minus)).fillna(0)
    df["adx"] = dx.ewm(span=ADX_PERIOD, adjust=False).mean()

    # EMA crossover signals (crossover on the last completed candle)
    df["cross_up"] = (df["ema_fast"] > df["ema_slow"]) & (df["ema_fast"].shift(1) <= df["ema_slow"].shift(1))
    df["cross_down"] = (df["ema_fast"] < df["ema_slow"]) & (df["ema_fast"].shift(1) >= df["ema_slow"].shift(1))

    return df


def get_trend(trend_df: pd.DataFrame) -> str:
    """Returns 'up', 'down', or 'neutral' based on H1 200 EMA."""
    trend_df = calculate_indicators(trend_df)
    last = trend_df.iloc[-1]
    if last["close"] > last["ema_trend"]:
        return "up"
    elif last["close"] < last["ema_trend"]:
        return "down"
    return "neutral"


def get_signal(signal_df: pd.DataFrame, trend: str):
    """Returns 'BUY', 'SELL', or None."""
    last = signal_df.iloc[-1]

    trend_allows_long = trend == "up"
    trend_allows_short = trend == "down"
    adx_ok = last["adx"] > ADX_MIN

    if last["cross_up"] and last["rsi"] > RSI_LONG_MIN and adx_ok and trend_allows_long:
        return "BUY"
    if last["cross_down"] and last["rsi"] < RSI_SHORT_MAX and adx_ok and trend_allows_short:
        return "SELL"
    return None


def calculate_sl_tp(entry: float, atr: float, signal: str) -> tuple[float, float]:
    if signal == "BUY":
        sl = entry - (atr * ATR_SL_MULT)
        tp = entry + (atr * ATR_TP_MULT)
    else:
        sl = entry + (atr * ATR_SL_MULT)
        tp = entry - (atr * ATR_TP_MULT)
    return round(sl, 5), round(tp, 5)
