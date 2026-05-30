"""Baseline model training + registration.

For each horizon we:
1. Build a pooled dataset across many tickers (features are scale-free).
2. Split each ticker chronologically (no shuffle) into train/test — evaluating
   on the most recent slice mimics real forward use and avoids leakage.
3. Fit classifier + regressor, evaluate vs naive baselines.
4. Refit on ALL data for the served model (standard once metrics are recorded).
5. Save the bundle and register it as the active artifact for that horizon.
"""

import logging
import math

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db.models.model_artifact import ModelArtifact
from app.ml import registry
from app.ml.features import FEATURE_COLS, HORIZON_DAYS, candles_to_frame, make_training_matrix
from app.ml.registry import ModelBundle
from app.services.indicators import compute_indicators
from app.services.market_data.base import MarketDataProvider

logger = logging.getLogger(__name__)

DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"]
TRAIN_FRACTION = 0.8
MIN_ROWS_PER_TICKER = 60


def train_and_register(
    db: Session,
    provider: MarketDataProvider,
    version: str,
    tickers: list[str] | None = None,
    lookback: str = "5y",
) -> dict:
    tickers = tickers or DEFAULT_TICKERS

    # Compute indicator frames once per ticker; reused across all horizons.
    frames: list[pd.DataFrame] = []
    for ticker in tickers:
        candles = provider.get_candles(ticker, lookback, "1d")
        if not candles:
            continue
        frames.append(compute_indicators(candles_to_frame(candles)))
    if not frames:
        raise RuntimeError("no training data fetched")

    summary: dict = {"version": version, "tickers": tickers, "horizons": {}}

    for horizon in HORIZON_DAYS:
        X_tr, yc_tr, yr_tr, X_te, yc_te, yr_te = _assemble(frames, horizon)

        clf = RandomForestClassifier(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=42, n_jobs=-1
        )
        reg = RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=42, n_jobs=-1
        )
        clf.fit(X_tr, yc_tr)
        reg.fit(X_tr, yr_tr)

        metrics = _evaluate(clf, reg, X_te, yc_te, yr_te, len(X_tr))

        # Refit on everything for the served model.
        X_all = pd.concat([X_tr, X_te])
        yc_all = pd.concat([yc_tr, yc_te])
        yr_all = pd.concat([yr_tr, yr_te])
        clf.fit(X_all, yc_all)
        reg.fit(X_all, yr_all)

        # Training-set feature stats power per-prediction z-score attribution.
        feature_means = {k: round(float(v), 6) for k, v in X_all.mean().items()}
        feature_stds = {k: round(float(v), 6) for k, v in X_all.std().items()}

        bundle = ModelBundle(
            horizon=horizon,
            classifier=clf,
            regressor=reg,
            feature_names=FEATURE_COLS,
            classes=list(clf.classes_),
            metrics=metrics,
            feature_means=feature_means,
            feature_stds=feature_stds,
        )
        path = registry.save_bundle(bundle, version)
        _register(db, version, horizon, path, metrics)
        summary["horizons"][horizon] = metrics
        logger.info("trained %s/%s: %s", version, horizon, metrics)

    return summary


def _assemble(frames: list[pd.DataFrame], horizon: str):
    parts = {"X_tr": [], "yc_tr": [], "yr_tr": [], "X_te": [], "yc_te": [], "yr_te": []}
    for ind in frames:
        X, yc, yr = make_training_matrix(ind, horizon)
        if len(X) < MIN_ROWS_PER_TICKER:
            continue
        cut = int(len(X) * TRAIN_FRACTION)
        parts["X_tr"].append(X.iloc[:cut])
        parts["yc_tr"].append(yc.iloc[:cut])
        parts["yr_tr"].append(yr.iloc[:cut])
        parts["X_te"].append(X.iloc[cut:])
        parts["yc_te"].append(yc.iloc[cut:])
        parts["yr_te"].append(yr.iloc[cut:])

    if not parts["X_tr"]:
        raise RuntimeError(f"insufficient data for horizon {horizon}")

    return (
        pd.concat(parts["X_tr"]),
        pd.concat(parts["yc_tr"]),
        pd.concat(parts["yr_tr"]),
        pd.concat(parts["X_te"]),
        pd.concat(parts["yc_te"]),
        pd.concat(parts["yr_te"]),
    )


def _evaluate(clf, reg, X_te, yc_te, yr_te, n_train: int) -> dict:
    clf_pred = clf.predict(X_te)
    reg_pred = reg.predict(X_te)

    # Naive baselines for honest comparison.
    majority_class = yc_te.mode().iloc[0]
    baseline_acc = float((yc_te == majority_class).mean())
    baseline_mae = float(yr_te.abs().mean())  # predicting "0 return"

    return {
        "n_train": int(n_train),
        "n_test": int(len(X_te)),
        "classifier": {
            "accuracy": round(float(accuracy_score(yc_te, clf_pred)), 4),
            "f1_macro": round(float(f1_score(yc_te, clf_pred, average="macro")), 4),
            "baseline_accuracy": round(baseline_acc, 4),
        },
        "regressor": {
            "mae": round(float(mean_absolute_error(yr_te, reg_pred)), 5),
            "rmse": round(math.sqrt(mean_squared_error(yr_te, reg_pred)), 5),
            "r2": round(float(r2_score(yr_te, reg_pred)), 4),
            "baseline_mae": round(baseline_mae, 5),
        },
    }


def _register(db: Session, version: str, horizon: str, path: str, metrics: dict) -> None:
    # Deactivate any currently-active artifact for this horizon.
    db.execute(
        update(ModelArtifact)
        .where(ModelArtifact.horizon == horizon, ModelArtifact.is_active.is_(True))
        .values(is_active=False)
    )
    db.add(
        ModelArtifact(
            model_version=version,
            horizon=horizon,
            path=path,
            metrics_json=metrics,
            feature_list_json=FEATURE_COLS,
            is_active=True,
        )
    )
    db.commit()


def predict_return_range(reg, X) -> tuple[float, float, float]:
    """Point estimate + uncertainty band from the spread across the forest's trees."""
    tree_preds = np.array([est.predict(X)[0] for est in reg.estimators_])
    mean = float(tree_preds.mean())
    std = float(tree_preds.std())
    return mean, mean - std, mean + std
