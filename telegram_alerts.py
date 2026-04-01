"""Telegram alerts for the OANDA trading bot — tagged [OANDA BOT]."""

import ssl
import json
import urllib.request
import urllib.parse
from datetime import datetime

TELEGRAM_TOKEN = "8728681717:AAEHB9prBm5OKHVWWftlECP9DdH-E16FAHE"
TELEGRAM_CHAT_ID = "5713165795"

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def send(text: str):
    try:
        params = urllib.parse.urlencode({
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       text,
            "parse_mode": "HTML",
        }).encode("utf-8")
        req = urllib.request.Request(f"{BASE_URL}/sendMessage", data=params, method="POST")
        with urllib.request.urlopen(req, timeout=10, context=SSL_CONTEXT) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        print(f"  Telegram error: {e}")
        return False


def alert_buy(instrument, units, entry, sl, tp):
    send(
        f"🟢 <b>[OANDA BOT] BUY</b>\n"
        f"Pair:        <b>{instrument}</b>\n"
        f"Units:       {units:,}\n"
        f"Entry:       {entry:.5f}\n"
        f"Stop Loss:   {sl:.5f}\n"
        f"Take Profit: {tp:.5f}\n"
        f"Time:        {datetime.utcnow().strftime('%H:%M UTC %d %b')}"
    )


def alert_sell(instrument, units, entry, sl, tp):
    send(
        f"🔴 <b>[OANDA BOT] SELL</b>\n"
        f"Pair:        <b>{instrument}</b>\n"
        f"Units:       {units:,}\n"
        f"Entry:       {entry:.5f}\n"
        f"Stop Loss:   {sl:.5f}\n"
        f"Take Profit: {tp:.5f}\n"
        f"Time:        {datetime.utcnow().strftime('%H:%M UTC %d %b')}"
    )


def alert_daily_summary(balance, nav, unrealized_pl, trades):
    emoji = "📈" if unrealized_pl >= 0 else "📉"
    send(
        f"{emoji} <b>[OANDA BOT] Daily Summary</b>\n"
        f"Date:         {datetime.utcnow().strftime('%d %b %Y')}\n"
        f"Balance:      £{balance:,.2f}\n"
        f"NAV:          £{nav:,.2f}\n"
        f"Unrealized:   £{unrealized_pl:+,.2f}\n"
        f"Trades today: {trades}"
    )
