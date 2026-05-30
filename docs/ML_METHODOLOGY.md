# ML Methodology

## Goal

Produce **interpretable, uncertainty-aware** short-horizon trend forecasts — not a trading edge. The system is designed to be honest about how often it's wrong.

## Features

Computed by `app/services/indicators.py` (the same code the dashboard uses) and assembled in `app/ml/features.py`. All features are **scale-free** so a single model generalizes across tickers:

- Trend: price / SMA7, / SMA30, / SMA100; SMA7 / SMA30; price / EMA20
- Momentum: RSI(14)/100; MACD and MACD-histogram normalized by price
- Volatility/position: 30d annualized volatility; Bollinger position; drawdown
- Volume: relative volume (vs 20d average)
- Lags: daily return at t, t-1 … t-4

## Labels

- **Regressor target:** forward return over the horizon, `close[t+h]/close[t] - 1`.
- **Classifier target:** bucketed from that return vs a per-horizon threshold (0.5% / 2% / 4% for 1d/7d/30d) → `bullish` / `bearish` / `neutral`.

## Models

`RandomForestClassifier` (direction) + `RandomForestRegressor` (return), one pair per horizon (1d/7d/30d). Pooled across a basket of tickers.

- **Confidence** = classifier's max class probability.
- **Expected return range** = mean ± std across the regressor's trees (the forest's own uncertainty).

## Train / test discipline

- **No leakage:** features at row `t` use only data ≤ `t`; labels are forward returns; the last `h` rows (no future) are dropped.
- **Chronological split** per ticker (no shuffling) for evaluation; final served model refits on all data.
- Metrics recorded per training run in `model_artifacts.metrics_json`: classifier accuracy + macro-F1 vs majority-class baseline; regressor MAE/RMSE/R² vs zero-return baseline.

## Explainability

Per-prediction signed attribution (dependency-free, SHAP-style):

```
contribution(feature) = global_importance(feature) × z_score(feature value)
```

where the z-score uses the training-set mean/std stored in the model bundle. This is directional and specific to the current input. A future upgrade could swap in `shap.TreeExplainer`.

## Backtesting (the honesty layer)

`app/ml/backtest.py` runs **walk-forward**:

- At each origin, train only on data strictly before it (no lookahead).
- Origins are spaced by the horizon → non-overlapping, independent forward returns → an honest equity curve.
- Metrics vs **three baselines**: majority-class, persistence ("tomorrow = today"), zero-return.
- Equity curve compares a long/flat strategy (long only when predicting bullish) to buy-and-hold.

## Why predictions are uncertain

Markets are near-efficient; short-horizon direction is close to random. On the synthetic `fake` provider (a pure random walk) the models **correctly fail to beat naive baselines** — if they "won," that would signal leakage or overfitting. On real data, a baseline RandomForest still won't be reliably profitable. The product never hides this: confidence scores, expected ranges, uncertainty notes, baseline comparisons, and the Model Transparency page all communicate it.

## Limitations

- Limited training history; not all market regimes represented.
- Lexicon sentiment is coarse (FinBERT/LLM = upgrade).
- No transaction costs/slippage modeled in the backtest equity curve.
- Educational only — not investment advice.
