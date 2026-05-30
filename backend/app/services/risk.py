"""Composite risk engine.

Risk is a transparent weighted blend of sub-scores (each 0-100), not a black box.
Every factor that goes in comes back out in the breakdown, so the UI can explain
*why* a stock is risky. Sentiment is added as a factor in Phase 7.

Inputs are the indicator `latest` snapshot + `signals` dict (from indicator_service)
and, optionally, model confidence from a prediction.
"""

# Full weights; only factors we actually have are used, then renormalized.
_WEIGHTS = {
    "volatility": 0.25,
    "drawdown": 0.22,
    "volume": 0.12,
    "trend": 0.12,
    "uncertainty": 0.16,
    "sentiment": 0.13,
}


def _clamp(x: float) -> float:
    return max(0.0, min(100.0, x))


def _level(score: float) -> str:
    if score < 25:
        return "low"
    if score < 50:
        return "medium"
    if score < 75:
        return "high"
    return "very_high"


def compute_risk(
    latest: dict,
    signals: dict,
    confidence: float | None = None,
    sentiment_score: float | None = None,
) -> dict:
    """Return {risk_score, risk_level, factors[]}.

    `latest` keys used: volatility_30, drawdown, relative_volume.
    `signals` keys used: above_sma_100, trend, rsi_zone, volume_spike.
    `sentiment_score` in [-1, 1]: negative news -> higher risk.
    """
    factors: list[dict] = []

    # --- Volatility: annualized %; 60% maps to max risk. ---
    vol = latest.get("volatility_30")
    if vol is not None:
        score = _clamp(vol / 60 * 100)
        factors.append(
            _factor("volatility", score, f"30-day volatility ~{vol:.0f}% annualized")
        )

    # --- Drawdown: depth below recent peak; 50% maps to max risk. ---
    dd = latest.get("drawdown")
    if dd is not None:
        score = _clamp(abs(dd) / 50 * 100)
        factors.append(_factor("drawdown", score, f"{abs(dd):.0f}% below recent peak"))

    # --- Volume: relative to average; 3x maps to max risk. ---
    rv = latest.get("relative_volume")
    if rv is not None:
        score = _clamp((rv - 1) / 2 * 100)
        spike = signals.get("volume_spike")
        desc = "Unusual volume spike" if spike else f"Volume ~{rv:.1f}x average"
        factors.append(_factor("volume", score, desc))

    # --- Trend / momentum: below long MA + downtrend + RSI extreme. ---
    trend_score = 0.0
    bits = []
    if signals.get("above_sma_100") is False:
        trend_score += 50
        bits.append("below 100-day average")
    if signals.get("trend") == "down":
        trend_score += 30
        bits.append("downtrend")
    if signals.get("rsi_zone") in ("overbought", "oversold"):
        trend_score += 20
        bits.append(f"RSI {signals['rsi_zone']}")
    if signals.get("above_sma_100") is not None:
        desc = "Trend: " + (", ".join(bits) if bits else "constructive")
        factors.append(_factor("trend", _clamp(trend_score), desc))

    # --- Model uncertainty: lower confidence -> higher risk. ---
    if confidence is not None:
        score = _clamp((1 - confidence) * 100)
        factors.append(
            _factor("uncertainty", score, f"Model confidence {confidence * 100:.0f}%")
        )

    # --- News sentiment: -1 (very negative) -> 100, +1 (very positive) -> 0. ---
    if sentiment_score is not None:
        score = _clamp((1 - sentiment_score) / 2 * 100)
        if sentiment_score < -0.1:
            tone = "negative"
        elif sentiment_score > 0.1:
            tone = "positive"
        else:
            tone = "neutral"
        factors.append(_factor("sentiment", score, f"News sentiment is {tone}"))

    risk_score = _aggregate(factors)
    return {
        "risk_score": round(risk_score, 1),
        "risk_level": _level(risk_score),
        "factors": factors,
    }


def _factor(name: str, score: float, description: str) -> dict:
    return {
        "name": name,
        "score": round(score, 1),
        "weight": _WEIGHTS[name],
        "description": description,
    }


def _aggregate(factors: list[dict]) -> float:
    if not factors:
        return 0.0
    total_weight = sum(f["weight"] for f in factors)
    weighted = sum(f["score"] * f["weight"] for f in factors)
    score = weighted / total_weight
    # Record each factor's normalized contribution in points for the UI.
    for f in factors:
        f["points"] = round(f["score"] * f["weight"] / total_weight, 1)
    return score
