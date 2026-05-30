"""Per-prediction explanation.

We approximate SHAP-style attribution cheaply and dependency-free:

    contribution(feature) = importance(feature) x z_score(feature value)

- importance: how much the model relies on the feature overall (global).
- z-score: how unusual THIS value is vs the training distribution (per-prediction).

Their product is signed: a feature that's both important and far above its norm
gets a large positive contribution. This gives a directional, ranked explanation
specific to the current input. (A future upgrade could swap in shap.TreeExplainer.)
"""


def describe_factor(feature: str, value: float) -> str:
    v = value
    match feature:
        case "rsi":
            pct = v * 100
            zone = "overbought" if pct >= 70 else "oversold" if pct <= 30 else "neutral momentum"
            return f"RSI is around {pct:.0f} ({zone})"
        case "ret_close_sma30":
            return f"Price is {'above' if v > 0 else 'below'} its 30-day moving average"
        case "ret_close_sma100":
            return f"Price is {'above' if v > 0 else 'below'} its 100-day moving average"
        case "ret_close_sma7":
            return f"Price is {'above' if v > 0 else 'below'} its 7-day moving average"
        case "ret_close_ema20":
            return f"Price is {'above' if v > 0 else 'below'} its 20-day EMA"
        case "ret_sma7_sma30":
            return f"Short-term trend is {'rising' if v > 0 else 'falling'} vs the medium-term"
        case "macd_norm" | "macd_hist_norm":
            return f"MACD momentum is {'bullish' if v > 0 else 'bearish'}"
        case "bb_pos":
            if v > 0.5:
                return "Price is in the upper Bollinger band region"
            if v < -0.5:
                return "Price is in the lower Bollinger band region"
            return "Price is near the middle of its Bollinger bands"
        case "volatility":
            return f"30-day volatility is about {v * 100:.0f}% annualized"
        case "drawdown_n":
            return f"Price is about {abs(v) * 100:.0f}% below its recent peak"
        case "rel_volume":
            return f"Volume is about {v:.1f}x its recent average"
        case _:
            direction = "elevated" if v > 0 else "depressed"
            return f"{feature} is {direction}"


def top_contributions(bundle, X, n: int = 5) -> list[dict]:
    """Top-n signed feature contributions for a single prediction row."""
    importances = bundle.classifier.feature_importances_
    means = getattr(bundle, "feature_means", None)
    stds = getattr(bundle, "feature_stds", None)
    row = X.iloc[0]

    items: list[dict] = []
    for i, name in enumerate(bundle.feature_names):
        value = float(row[name])
        importance = float(importances[i])
        if means and stds and name in means:
            std = stds.get(name) or 1.0
            z = (value - means[name]) / (std if std != 0 else 1.0)
        else:
            z = 0.0
        contribution = importance * z
        items.append(
            {
                "feature": name,
                "value": round(value, 4),
                "importance": round(importance, 4),
                "contribution": round(contribution, 4),
                "direction": "elevated" if z > 0 else "depressed",
                "description": describe_factor(name, value),
            }
        )

    # If we have z-scores, rank by attribution magnitude; otherwise by importance.
    if means and stds:
        items.sort(key=lambda d: abs(d["contribution"]), reverse=True)
    else:
        items.sort(key=lambda d: d["importance"], reverse=True)
    return items[:n]


def uncertainty_note(confidence: float, class_probs: dict, volatility: float | None) -> str:
    """Plain-English calibration language for the forecast."""
    sorted_p = sorted(class_probs.values(), reverse=True)
    margin = sorted_p[0] - sorted_p[1] if len(sorted_p) > 1 else sorted_p[0]

    if confidence < 0.45 or margin < 0.1:
        base = "The model is highly uncertain — outcomes are nearly evenly split."
    elif confidence < 0.6:
        base = "Moderate confidence; other outcomes remain meaningfully likely."
    else:
        base = "Relatively confident, but this is still a probabilistic estimate."

    if volatility is not None and volatility > 40:
        base += " Elevated volatility widens the range of plausible outcomes."
    return base
