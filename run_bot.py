"""Main OANDA bot loop."""

import time
from datetime import datetime, timezone

import oandapyV20

from config import (
    INSTRUMENTS, SIGNAL_GRANULARITY, TREND_GRANULARITY,
    CANDLE_COUNT, UNITS, MAX_OPEN_POSITIONS,
    DAILY_LOSS_LIMIT_PCT, SCAN_INTERVAL,
)
from broker import (
    get_client, get_candles, get_account_summary,
    get_open_positions, is_flat, place_order, get_daily_pl,
)
from strategy import calculate_indicators, get_trend, get_signal, calculate_sl_tp


def now_et() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M UTC")


def print_header():
    print("╔══════════════════════════════════════════════╗")
    print("║         OANDA TRADING BOT                   ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"  Instruments : {', '.join(INSTRUMENTS)}")
    print(f"  Signal TF   : {SIGNAL_GRANULARITY} | Trend TF: {TREND_GRANULARITY}")
    print(f"  Scan every  : {SCAN_INTERVAL}s")
    print(f"  Stop        : Ctrl+C\n")


def main():
    print_header()
    client = get_client()

    # Get starting balance for daily loss circuit breaker
    summary = get_account_summary(client)
    starting_balance = summary["balance"]
    print(f"  Account balance : £{starting_balance:,.2f}")
    print(f"  Daily loss limit: {DAILY_LOSS_LIMIT_PCT*100:.1f}% (£{starting_balance * DAILY_LOSS_LIMIT_PCT:,.2f})\n")

    while True:
        try:
            now = now_et()
            print(f"\n  [{now}] Scanning {len(INSTRUMENTS)} instrument(s)...")

            # Daily loss circuit breaker
            daily_pl = get_daily_pl(client)
            if daily_pl < -(starting_balance * DAILY_LOSS_LIMIT_PCT):
                print(f"  *** DAILY LOSS LIMIT HIT (P&L: £{daily_pl:.2f}) — no new trades today ***")
                time.sleep(SCAN_INTERVAL)
                continue

            open_positions = get_open_positions(client)
            open_count = len(open_positions)

            if open_count >= MAX_OPEN_POSITIONS:
                print(f"  Max positions reached ({open_count}/{MAX_OPEN_POSITIONS}) — skipping new entries")
                time.sleep(SCAN_INTERVAL)
                continue

            for instrument in INSTRUMENTS:
                try:
                    # Fetch candles for both timeframes
                    signal_df = get_candles(client, instrument, SIGNAL_GRANULARITY, CANDLE_COUNT)
                    trend_df = get_candles(client, instrument, TREND_GRANULARITY, CANDLE_COUNT)

                    if signal_df.empty or trend_df.empty:
                        print(f"  {instrument}: No data returned — skipping")
                        continue

                    # Calculate indicators
                    signal_df = calculate_indicators(signal_df)
                    trend = get_trend(trend_df)

                    # Get signal
                    signal = get_signal(signal_df, trend)
                    last = signal_df.iloc[-1]

                    if signal is None:
                        print(f"  {instrument}: No signal | EMA {last['ema_fast']:.5f}/{last['ema_slow']:.5f} | RSI {last['rsi']:.1f} | ADX {last['adx']:.1f} | Trend {trend}")
                        continue

                    # Check if already in this instrument
                    if not is_flat(client, instrument):
                        print(f"  {instrument}: Already in position — skipping")
                        continue

                    # Calculate entry, SL, TP
                    entry = last["close"]
                    atr = last["atr"]
                    sl, tp = calculate_sl_tp(entry, atr, signal)

                    # Place order
                    rv = place_order(client, instrument, signal, sl, tp, UNITS)
                    arrow = "🟢 BUY " if signal == "BUY" else "🔴 SELL"
                    print(f"  {arrow} {instrument} @ {entry:.5f} | SL={sl:.5f} | TP={tp:.5f} | ATR={atr:.5f}")

                except oandapyV20.exceptions.V20Error as e:
                    print(f"  {instrument}: API error — {e}")
                except Exception as e:
                    print(f"  {instrument}: Error — {e}")

        except KeyboardInterrupt:
            print("\n\n  Bot stopped.")
            break
        except Exception as e:
            print(f"  Unexpected error: {e}")

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
