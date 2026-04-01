"""OANDA bot configuration."""

OANDA_API_TOKEN = "d7d399666cd4efbf036538688658dd5a-f1021ab40c1cb517b2c7418a87bbc5e2"
OANDA_ACCOUNT_ID = "101-004-38955730-001"
OANDA_ENVIRONMENT = "practice"  # "practice" for demo, "live" for real money

# Instruments to trade
INSTRUMENTS = ["EUR_USD"]

# Timeframes
SIGNAL_GRANULARITY = "M15"   # Signal timeframe
TREND_GRANULARITY = "H1"     # Macro trend filter timeframe
CANDLE_COUNT = 220           # Enough for 200 EMA + buffer

# Strategy parameters
EMA_FAST = 9
EMA_SLOW = 21
EMA_TREND = 200
RSI_PERIOD = 14
RSI_LONG_MIN = 50      # RSI must be above this for longs
RSI_SHORT_MAX = 50     # RSI must be below this for shorts
ATR_PERIOD = 14
ATR_SL_MULT = 1.5      # Stop loss = 1.5x ATR
ATR_TP_MULT = 4.5      # Take profit = 3:1 reward/risk (4.5x ATR)
ADX_PERIOD = 14
ADX_MIN = 20           # Minimum ADX to confirm trend strength

# Risk management
UNITS = 10000          # Units per trade (~£1000 equivalent at 10:1 margin)
MAX_OPEN_POSITIONS = 3
DAILY_LOSS_LIMIT_PCT = 0.03   # 3% daily loss circuit breaker

# Bot settings
SCAN_INTERVAL = 60     # Seconds between scans
