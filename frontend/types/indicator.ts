// Mirrors backend/app/schemas/indicator.py

export interface IndicatorPoint {
  timestamp: string;
  sma_7: number | null;
  sma_30: number | null;
  sma_100: number | null;
  ema_20: number | null;
  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
  bollinger_mid: number | null;
  bollinger_upper: number | null;
  bollinger_lower: number | null;
  volatility_30: number | null;
  drawdown: number | null;
  daily_return: number | null;
  relative_volume: number | null;
}

export interface IndicatorLatest extends IndicatorPoint {
  close: number | null;
  max_drawdown: number | null;
}

export interface IndicatorSignals {
  rsi_zone: "overbought" | "oversold" | "neutral" | null;
  macd_bullish: boolean | null;
  above_sma_30: boolean | null;
  above_sma_100: boolean | null;
  trend: "up" | "down" | null;
  volume_spike: boolean | null;
}

export interface Indicators {
  ticker: string;
  range: string;
  interval: string;
  latest: IndicatorLatest;
  signals: IndicatorSignals;
  series: IndicatorPoint[];
}
