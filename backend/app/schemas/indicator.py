from pydantic import BaseModel


class IndicatorPoint(BaseModel):
    timestamp: str
    sma_7: float | None = None
    sma_30: float | None = None
    sma_100: float | None = None
    ema_20: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    bollinger_mid: float | None = None
    bollinger_upper: float | None = None
    bollinger_lower: float | None = None
    volatility_30: float | None = None
    drawdown: float | None = None
    daily_return: float | None = None
    relative_volume: float | None = None


class IndicatorLatest(IndicatorPoint):
    close: float | None = None
    max_drawdown: float | None = None


class IndicatorSignals(BaseModel):
    rsi_zone: str | None = None  # overbought / oversold / neutral
    macd_bullish: bool | None = None
    above_sma_30: bool | None = None
    above_sma_100: bool | None = None
    trend: str | None = None  # up / down
    volume_spike: bool | None = None


class IndicatorsOut(BaseModel):
    ticker: str
    range: str
    interval: str
    latest: IndicatorLatest
    signals: IndicatorSignals
    series: list[IndicatorPoint]
