"""OANDA API connection, data fetching, and order management."""

import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.trades as trades
from oandapyV20.contrib.requests import (
    MarketOrderRequest,
    StopLossDetails,
    TakeProfitDetails,
)
import pandas as pd

from config import OANDA_API_TOKEN, OANDA_ACCOUNT_ID, OANDA_ENVIRONMENT


def get_client():
    return oandapyV20.API(access_token=OANDA_API_TOKEN, environment=OANDA_ENVIRONMENT)


def get_candles(client, instrument: str, granularity: str, count: int) -> pd.DataFrame:
    params = {"granularity": granularity, "count": count}
    r = instruments.InstrumentsCandles(instrument=instrument, params=params)
    client.request(r)
    candles = [c for c in r.response["candles"] if c["complete"]]
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame({
        "time":   [c["time"] for c in candles],
        "open":   [float(c["mid"]["o"]) for c in candles],
        "high":   [float(c["mid"]["h"]) for c in candles],
        "low":    [float(c["mid"]["l"]) for c in candles],
        "close":  [float(c["mid"]["c"]) for c in candles],
        "volume": [c["volume"] for c in candles],
    })
    return df


def get_account_summary(client) -> dict:
    r = accounts.AccountSummary(OANDA_ACCOUNT_ID)
    rv = client.request(r)
    acc = rv["account"]
    return {
        "balance":          float(acc["balance"]),
        "nav":              float(acc["NAV"]),
        "unrealized_pl":    float(acc["unrealizedPL"]),
        "open_trade_count": int(acc["openTradeCount"]),
    }


def get_open_positions(client) -> dict:
    """Returns dict of {instrument: {'units': float, 'side': 'long'/'short'}}"""
    r = positions.OpenPositions(accountID=OANDA_ACCOUNT_ID)
    rv = client.request(r)
    result = {}
    for pos in rv["positions"]:
        long_units = int(pos["long"]["units"])
        short_units = int(pos["short"]["units"])
        if long_units != 0:
            result[pos["instrument"]] = {"units": long_units, "side": "long"}
        elif short_units != 0:
            result[pos["instrument"]] = {"units": short_units, "side": "short"}
    return result


def is_flat(client, instrument: str) -> bool:
    open_pos = get_open_positions(client)
    return instrument not in open_pos


def place_order(client, instrument: str, signal: str, sl_price: float, tp_price: float, units: int) -> dict:
    trade_units = units if signal == "BUY" else -units
    order = MarketOrderRequest(
        instrument=instrument,
        units=trade_units,
        stopLossOnFill=StopLossDetails(price=round(sl_price, 5)).data,
        takeProfitOnFill=TakeProfitDetails(price=round(tp_price, 5)).data,
    )
    r = orders.OrderCreate(OANDA_ACCOUNT_ID, data=order.data)
    rv = client.request(r)
    return rv


def get_daily_pl(client) -> float:
    """Approximate daily P&L from open trades unrealized + today's closed."""
    r = accounts.AccountSummary(OANDA_ACCOUNT_ID)
    rv = client.request(r)
    return float(rv["account"]["unrealizedPL"])
