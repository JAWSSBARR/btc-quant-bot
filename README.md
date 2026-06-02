# BTC Quant Bot

An open-source Bitcoin market-analysis bot that pulls live data from multiple
free public sources, computes technical indicators, runs the combined picture
through an LLM analyst, and delivers a structured recommendation to Telegram.

It is built for transparency: every data source is free and public, the
analytical context lives in a human-readable JSON file you control, and the
bot never places trades — it only produces analysis.

---

## What problem it solves

Manually checking spot/futures prices, funding rates, options volatility,
on-chain fees, and the Fear & Greed index before every trading decision is
slow and easy to do inconsistently. This bot collects all of it in one pass,
applies a fixed analytical framework, and outputs a consistent, weighted
recommendation (LONG / SHORT / WAIT) with explicit invalidation levels — on a
schedule, straight to your Telegram channel.

## Data sources (all free)

| Source | Data |
|---|---|
| Binance | spot price, futures price, funding rate, OHLCV candles |
| Deribit | BTC volatility index (DVOL) |
| mempool.space | on-chain fees, hashrate |
| blockchain.com | mempool / unconfirmed tx |
| Alternative.me | Fear & Greed index |
| FRED | macro series (Fed funds rate, CPI) — optional |

## Architecture

```
data_fetcher.py   ->  collect live data from all sources
indicators.py     ->  SMA / EMA / RSI / Fibonacci / anchored VWAP
claude_analyst.py ->  send snapshot + context to the LLM, get structured JSON
telegram_sender.py->  format and deliver the report
main.py           ->  orchestrate (datacheck | once | schedule)
handoff_context.json -> persistent analytical memory between runs
```

## Setup

```bash
# 1. install dependencies
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. configure secrets
cp .env.example .env
# open .env and fill in ANTHROPIC_API_KEY, and optionally Telegram + FRED keys
```

## Usage

```bash
# fetch data only — no LLM cost, good for verifying sources work
python main.py datacheck

# run one full analysis (calls the LLM once)
python main.py once

# run continuously on an interval (default every 4 hours)
python main.py schedule
```

## Configuration

All configuration is read from environment variables (see `.env.example`):

- `ANTHROPIC_API_KEY` — required for analysis
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — optional, for delivery
- `FRED_API_KEY` — optional, enables macro data
- `RUN_INTERVAL_HOURS` — cadence for `schedule` mode

The analytical baseline (all-time high, cycle low, framework rules) lives in
`handoff_context.json`. Edit it to reflect your own evolving thesis; it acts
as the bot's memory between runs.

## Security notes

- Your real `.env` is git-ignored and never committed.
- No API keys are stored in code.
- The bot is read-only: it has no exchange trading permissions and places no orders.

## Disclaimer

This software is for informational and educational purposes only. It is not
financial advice. Cryptocurrency trading carries substantial risk. Use at your
own risk.

## License

MIT — see [LICENSE](LICENSE).

---

## 한국어 안내

비트코인 시장 데이터를 여러 무료 공개 소스에서 자동으로 수집하고, 기술적 지표를
계산한 뒤, 그 결과를 LLM 분석가에게 넘겨 구조화된 추천(LONG/SHORT/WAIT)을
텔레그램으로 보내주는 오픈소스 봇입니다. 봇은 절대 매매를 직접 실행하지 않으며
분석만 생성합니다.

### 빠른 시작

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # .env 에 키 입력
python main.py datacheck   # 데이터 수집만 (비용 0)
python main.py once        # 1회 분석
python main.py schedule    # 4시간 주기 운용
```

분석 기준선(ATH, 사이클 저점, 프레임워크 규칙)은 `handoff_context.json` 에
들어 있으며, 본인의 시장 관점에 맞게 수정하면 됩니다.
