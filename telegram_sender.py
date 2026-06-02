"""Send analysis reports to a Telegram chat / channel."""
import requests

import config


def send(text):
    """Send a plain-text message. Returns True on success, False otherwise."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[telegram] token/chat id not set, skipping send.")
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        r.raise_for_status()
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[telegram] send failed: {e}")
        return False


def format_report(result, snapshot):
    """Turn the structured result into a readable Telegram message."""
    price = snapshot.get("spot_price")
    action = result.get("action", "WAIT")
    conf = result.get("confidence", 0)

    lines = [
        "<b>BTC 분석 리포트</b>",
        f"현재가: ${price:,.0f}" if isinstance(price, (int, float)) else "현재가: N/A",
        f"추천: {action} (신뢰도 {conf}%)",
        "",
    ]

    scenarios = result.get("scenarios") or []
    if scenarios:
        lines.append("시나리오")
        for s in scenarios:
            lines.append(f"- {s.get('name')}: {s.get('probability')}%")
        lines.append("")

    report = result.get("report_ko")
    if report:
        lines.append(report)

    return "\n".join(lines)
