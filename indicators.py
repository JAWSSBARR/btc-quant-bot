"""Technical indicators computed from OHLCV candles.

Pure-python / pandas implementations so the project has no heavy
TA-library dependency. Input is the list of candle dicts returned by
data_fetcher.get_ohlcv().
"""
import pandas as pd


def _to_frame(candles):
    df = pd.DataFrame(candles)
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def sma(series, length):
    return series.rolling(window=length).mean()


def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()


def rsi(series, length=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=length).mean()
    loss = (-delta.clip(upper=0)).rolling(window=length).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def anchored_vwap(df, anchor_index=0):
    """Volume-weighted average price anchored from a chosen candle."""
    sub = df.iloc[anchor_index:]
    typical = (sub["high"] + sub["low"] + sub["close"]) / 3
    cum_vol = sub["volume"].cumsum()
    cum_pv = (typical * sub["volume"]).cumsum()
    return (cum_pv / cum_vol).iloc[-1]


def fib_levels(high, low):
    """Standard Fibonacci retracement levels between a swing high and low."""
    diff = high - low
    return {
        "0.0": high,
        "0.236": high - diff * 0.236,
        "0.382": high - diff * 0.382,
        "0.5": high - diff * 0.5,
        "0.618": high - diff * 0.618,
        "0.786": high - diff * 0.786,
        "1.0": low,
    }


def compute(candles):
    """Return a compact dict of indicators for the latest candle."""
    if not candles or len(candles) < 50:
        return {"error": "not enough candles"}

    df = _to_frame(candles)
    close = df["close"]

    swing_high = df["high"].max()
    swing_low = df["low"].min()

    return {
        "last_close": float(close.iloc[-1]),
        "sma_20": _last(sma(close, 20)),
        "sma_50": _last(sma(close, 50)),
        "sma_200": _last(sma(close, 200)),
        "ema_21": _last(ema(close, 21)),
        "rsi_14": _last(rsi(close, 14)),
        "anchored_vwap": float(anchored_vwap(df)),
        "swing_high": float(swing_high),
        "swing_low": float(swing_low),
        "fib": {k: round(v, 2) for k, v in fib_levels(swing_high, swing_low).items()},
    }


def _last(series):
    val = series.dropna()
    return float(val.iloc[-1]) if len(val) else None


if __name__ == "__main__":
    import json
    import data_fetcher
    candles = data_fetcher.get_ohlcv()
    print(json.dumps(compute(candles), indent=2))
