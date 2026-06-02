"""Claude-powered analysis layer.

Takes the market snapshot + computed indicators, sends them to Claude
with a persistent analytical context (handoff_context.json), and returns
a structured JSON recommendation plus a human-readable Korean report.

Prompt caching is used on the large, stable system context so repeated
runs stay cheap.
"""
import json
import os

from anthropic import Anthropic

import config

_HANDOFF_PATH = os.path.join(os.path.dirname(__file__), "handoff_context.json")

SYSTEM_INSTRUCTIONS = """You are a disciplined BTC derivatives analyst.
You evaluate the market across four axes: technical, derivatives, on-chain,
and macro. You always reason from data, assign explicit probability weights
to scenarios, and give one of three actions: LONG, SHORT, or WAIT.
You are risk-aware and never recommend a position without a clear invalidation
level. Respond ONLY with a single JSON object, no markdown, in this schema:

{
  "action": "LONG" | "SHORT" | "WAIT",
  "confidence": 0-100,
  "scenarios": [{"name": str, "probability": 0-100, "note": str}],
  "key_levels": {"support": [float], "resistance": [float], "invalidation": float},
  "driver_weights": {"technical": 0-100, "derivatives": 0-100, "onchain": 0-100, "macro": 0-100},
  "report_ko": "A concise Korean-language report for a Telegram channel."
}
"""


def _load_handoff():
    try:
        with open(_HANDOFF_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "{}"


def analyze(snapshot, indicators):
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    handoff = _load_handoff()

    user_payload = {
        "live_snapshot": snapshot,
        "indicators": indicators,
    }

    message = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=config.MAX_OUTPUT_TOKENS,
        system=[
            {"type": "text", "text": SYSTEM_INSTRUCTIONS},
            {
                "type": "text",
                "text": "Persistent analytical context:\n" + handoff,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            }
        ],
    )

    text = "".join(
        block.text for block in message.content if getattr(block, "type", "") == "text"
    )
    return _safe_parse(text)


def _safe_parse(text):
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"action": "WAIT", "confidence": 0, "report_ko": text, "_parse_error": True}
