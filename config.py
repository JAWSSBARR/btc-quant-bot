"""Central configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Anthropic ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_OUTPUT_TOKENS = 8192  # raised from 4096 to avoid truncated Korean reports

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- FRED (optional) ---
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# --- Scheduling ---
RUN_INTERVAL_HOURS = int(os.getenv("RUN_INTERVAL_HOURS", "4"))

# --- Market target ---
SYMBOL = "BTCUSDT"
OHLCV_INTERVAL = "4h"
OHLCV_LIMIT = 300
