"""Fetch live BTC market data from free public sources.

Sources (all free, most need no API key):
  - Binance        : spot price, futures price, OHLCV candles
  - Deribit        : options implied volatility (DVOL)
  - mempool.space  : on-chain fees / hashrate
  - blockchain.com : on-chain stats
  - Alternative.me : Fear & Greed index
  - FRED           : macro series (optional, needs free key)
"""
import time
import requests

import config

TIMEOUT = 15
HEADERS = {"User-Agent": "btc-quant-bot/1.0"}


def _get(url, params=None):
    """GET with a small retry loop so a single hiccup doesn't kill the run."""
    last_err = None
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed for {url}: {last_err}")


# --- Binance ---------------------------------------------------------------

def get_spot_price():
    data = _get("https://api.binance.com/api/v3/ticker/price",
                {"symbol": config.SYMBOL})
    return float(data["price"])


def get_futures_price():
    data = _get("https://fapi.binance.com/fapi/v1/ticker/price",
                {"symbol": config.SYMBOL})
    return float(data["price"])


def get_funding_rate():
    data = _get("https://fapi.binance.com/fapi/v1/premiumIndex",
                {"symbol": config.SYMBOL})
    return {
        "mark_price": float(data["markPrice"]),
        "last_funding_rate": float(data["lastFundingRate"]),
        "next_funding_time": int(data["nextFundingTime"]),
    }


def get_ohlcv():
    """Return list of [open_time, open, high, low, close, volume]."""
    raw = _get("https://api.binance.com/api/v3/klines", {
        "symbol": config.SYMBOL,
        "interval": config.OHLCV_INTERVAL,
        "limit": config.OHLCV_LIMIT,
    })
    candles = []
    for k in raw:
        candles.append({
            "open_time": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    return candles


# --- Deribit (volatility) --------------------------------------------------

def get_dvol():
    """Deribit BTC volatility index (DVOL), latest value."""
    now = int(time.time() * 1000)
    start = now - 6 * 60 * 60 * 1000  # last 6h
    data = _get("https://www.deribit.com/api/v2/public/get_volatility_index_data", {
        "currency": "BTC",
        "start_timestamp": start,
        "end_timestamp": now,
        "resolution": "3600",
    })
    candles = data.get("result", {}).get("data", [])
    if not candles:
        return None
    # each row: [timestamp, open, high, low, close]
    return float(candles[-1][4])


# --- On-chain --------------------------------------------------------------

def get_mempool_fees():
    return _get("https://mempool.space/api/v1/fees/recommended")


def get_hashrate():
    data = _get("https://mempool.space/api/v1/mining/hashrate/3d")
    return data.get("currentHashrate")


def get_onchain_stats():
    out = {}
    try:
        out["unconfirmed_tx"] = _get("https://blockchain.info/q/unconfirmedcount")
    except Exception:  # noqa: BLE001
        out["unconfirmed_tx"] = None
    return out


# --- Sentiment -------------------------------------------------------------

def get_fear_greed():
    data = _get("https://api.alternative.me/fng/", {"limit": 1})
    item = data["data"][0]
    return {"value": int(item["value"]), "classification": item["value_classification"]}


# --- Macro (optional) ------------------------------------------------------

def get_fred_series(series_id):
    if not config.FRED_API_KEY:
        return None
    data = _get("https://api.stlouisfed.org/fred/series/observations", {
        "series_id": series_id,
        "api_key": config.FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    })
    obs = data.get("observations", [])
    return obs[0]["value"] if obs else None


# --- Aggregate -------------------------------------------------------------

def fetch_all():
    """Collect every source into one dict. Individual failures are tolerated."""
    snapshot = {"timestamp": int(time.time())}

    def safe(name, fn):
        try:
            snapshot[name] = fn()
        except Exception as e:  # noqa: BLE001
            snapshot[name] = {"error": str(e)}

    safe("spot_price", get_spot_price)
    safe("futures_price", get_futures_price)
    safe("funding", get_funding_rate)
    safe("ohlcv", get_ohlcv)
    safe("dvol", get_dvol)
    safe("mempool_fees", get_mempool_fees)
    safe("hashrate", get_hashrate)
    safe("onchain", get_onchain_stats)
    safe("fear_greed", get_fear_greed)

    snapshot["macro"] = {
        "fed_funds_rate": get_fred_series("DFF"),
        "cpi": get_fred_series("CPIAUCSL"),
    }
    return snapshot


if __name__ == "__main__":
    import json
    snap = fetch_all()
    # Trim OHLCV for readable printing
    if isinstance(snap.get("ohlcv"), list):
        snap["ohlcv"] = f"{len(snap['ohlcv'])} candles"
    print(json.dumps(snap, indent=2, ensure_ascii=False))
