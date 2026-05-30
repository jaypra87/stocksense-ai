"""Walk-forward backtesting.

At each historical origin we train ONLY on data strictly before it, predict the
forward return/direction, and compare to what actually happened. Origins are
spaced by the horizon so the forward returns don't overlap — that keeps the
equity curve and metrics honest.

This is deliberately separate from the served global model: a per-ticker
walk-forward is the clean way to ask "would this approach have worked on this
stock, using only information available at the time?"
"""

import math
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from app.ml.features import HORIZON_DAYS, make_training_matrix

MIN_TRAIN = 120
MAX_ORIGINS = 300  # cap predictions to bound runtime
MAX_RETRAINS = 40  # cap model refits to bound runtime


class NotEnoughDataError(Exception):
    """Not enough history to run a meaningful backtest."""


def _fit(X, yc, yr):
    # Lighter forest than the served model — backtest refits many times.
    clf = RandomForestClassifier(
        n_estimators=60, max_depth=6, min_samples_leaf=15, random_state=42, n_jobs=-1
    )
    reg = RandomForestRegressor(
        n_estimators=60, max_depth=6, min_samples_leaf=15, random_state=42, n_jobs=-1
    )
    clf.fit(X, yc)
    reg.fit(X, yr)
    return clf, reg


def run_walk_forward(indicators_df: pd.DataFrame, horizon: str) -> dict:
    X, yc, yr = make_training_matrix(indicators_df, horizon)
    days = HORIZON_DAYS[horizon]
    n = len(X)
    if n < MIN_TRAIN + days + 5:
        raise NotEnoughDataError(f"need >{MIN_TRAIN + days + 5} usable rows, have {n}")

    # Non-overlapping origins: step by the horizon so forward returns are independent.
    origins = list(range(MIN_TRAIN, n, days))
    if len(origins) > MAX_ORIGINS:
        origins = origins[-MAX_ORIGINS:]
    retrain_every = max(1, math.ceil(len(origins) / MAX_RETRAINS))

    clf = reg = None
    records: list[dict] = []
    for k, i in enumerate(origins):
        if k % retrain_every == 0:
            clf, reg = _fit(X.iloc[:i], yc.iloc[:i], yr.iloc[:i])
        xrow = X.iloc[[i]]
        records.append(
            {
                "date": X.index[i].date().isoformat(),
                "pred_trend": str(clf.predict(xrow)[0]),
                "actual_trend": str(yc.iloc[i]),
                "pred_return": round(float(reg.predict(xrow)[0]), 5),
                "actual_return": round(float(yr.iloc[i]), 5),
            }
        )

    metrics, chart = _summarize(records)
    return {
        "horizon": horizon,
        "start_date": records[0]["date"],
        "end_date": records[-1]["date"],
        "metrics": metrics,
        "chart_data": chart,
    }


def _summarize(records: list[dict]) -> tuple[dict, dict]:
    n = len(records)
    pred_t = [r["pred_trend"] for r in records]
    act_t = [r["actual_trend"] for r in records]
    pred_r = np.array([r["pred_return"] for r in records])
    act_r = np.array([r["actual_return"] for r in records])

    correct = [p == a for p, a in zip(pred_t, act_t, strict=True)]
    accuracy = sum(correct) / n

    # Baselines.
    majority = Counter(act_t).most_common(1)[0][0]
    baseline_acc = sum(a == majority for a in act_t) / n
    persistence_acc = (
        sum(act_t[i - 1] == act_t[i] for i in range(1, n)) / (n - 1) if n > 1 else 0.0
    )

    mae = float(np.mean(np.abs(pred_r - act_r)))
    rmse = float(np.sqrt(np.mean((pred_r - act_r) ** 2)))
    baseline_mae = float(np.mean(np.abs(act_r)))  # predicting zero return

    # Equity: go long only when predicting bullish, vs passive buy-and-hold.
    model_eq = buy_hold = 1.0
    running_correct = 0
    equity, cum_acc = [], []
    for idx, r in enumerate(records):
        position = 1.0 if r["pred_trend"] == "bullish" else 0.0
        model_eq *= 1 + position * r["actual_return"]
        buy_hold *= 1 + r["actual_return"]
        equity.append(
            {
                "date": r["date"],
                "model": round((model_eq - 1) * 100, 2),
                "buy_hold": round((buy_hold - 1) * 100, 2),
            }
        )
        running_correct += int(correct[idx])
        cum_acc.append({"date": r["date"], "accuracy": round(running_correct / (idx + 1) * 100, 1)})

    metrics = {
        "n_predictions": n,
        "directional_accuracy": round(accuracy * 100, 1),
        "baseline_accuracy": round(baseline_acc * 100, 1),
        "persistence_accuracy": round(persistence_acc * 100, 1),
        "mae": round(mae, 5),
        "rmse": round(rmse, 5),
        "baseline_mae": round(baseline_mae, 5),
        "beats_baseline": accuracy > baseline_acc,
    }
    chart = {"returns": records, "equity": equity, "cumulative_accuracy": cum_acc}
    return metrics, chart
