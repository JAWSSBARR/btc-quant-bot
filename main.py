"""BTC Quant Bot - entry point.

Usage:
    python main.py datacheck   # fetch data only, no API cost
    python main.py once        # run one full analysis
    python main.py schedule    # run on an interval (default every 4h)
"""
import json
import sys
import time

import config
import data_fetcher
import indicators
import telegram_sender


def run_datacheck():
    snap = data_fetcher.fetch_all()
    if isinstance(snap.get("ohlcv"), list):
        snap["ohlcv"] = f"{len(snap['ohlcv'])} candles"
    print(json.dumps(snap, indent=2, ensure_ascii=False))
    print("\n[datacheck] done. No API cost incurred.")


def run_once():
    print("[1/4] fetching market data...")
    snap = data_fetcher.fetch_all()

    print("[2/4] computing indicators...")
    ind = indicators.compute(snap.get("ohlcv") or [])

    print("[3/4] running Claude analysis...")
    # imported lazily so `datacheck` works without the anthropic SDK installed
    import claude_analyst
    result = claude_analyst.analyze(snap, ind)

    print("[4/4] sending report...")
    message = telegram_sender.format_report(result, snap)
    telegram_sender.send(message)

    print("\n" + "=" * 50)
    print(message)
    print("=" * 50)
    return result


def run_schedule():
    interval = config.RUN_INTERVAL_HOURS * 3600
    print(f"[schedule] running every {config.RUN_INTERVAL_HOURS}h. Ctrl-C to stop.")
    while True:
        try:
            run_once()
        except Exception as e:  # noqa: BLE001
            print(f"[schedule] run failed: {e}")
        time.sleep(interval)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if mode == "datacheck":
        run_datacheck()
    elif mode == "once":
        run_once()
    elif mode == "schedule":
        run_schedule()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
