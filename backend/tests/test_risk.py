from app.services.risk import compute_risk


def _latest(vol=20.0, dd=-5.0, rv=1.0):
    return {"volatility_30": vol, "drawdown": dd, "relative_volume": rv}


def _signals(above100=True, trend="up", rsi_zone="neutral", spike=False):
    return {
        "above_sma_100": above100,
        "trend": trend,
        "rsi_zone": rsi_zone,
        "volume_spike": spike,
    }


def test_low_risk_calm_uptrend() -> None:
    risk = compute_risk(_latest(vol=12, dd=-3, rv=1.0), _signals())
    assert risk["risk_level"] in ("low", "medium")
    assert 0 <= risk["risk_score"] <= 100


def test_high_risk_volatile_drawdown_downtrend() -> None:
    risk = compute_risk(
        _latest(vol=70, dd=-45, rv=3.5),
        _signals(above100=False, trend="down", rsi_zone="oversold", spike=True),
    )
    assert risk["risk_score"] > 60
    assert risk["risk_level"] in ("high", "very_high")


def test_score_is_monotonic_in_volatility() -> None:
    low = compute_risk(_latest(vol=10), _signals())["risk_score"]
    high = compute_risk(_latest(vol=55), _signals())["risk_score"]
    assert high > low


def test_model_uncertainty_raises_risk() -> None:
    base = compute_risk(_latest(), _signals())["risk_score"]
    uncertain = compute_risk(_latest(), _signals(), confidence=0.34)["risk_score"]
    assert uncertain > base


def test_factor_breakdown_present_and_weighted() -> None:
    risk = compute_risk(_latest(), _signals(), confidence=0.7)
    names = {f["name"] for f in risk["factors"]}
    assert {"volatility", "drawdown", "volume", "trend", "uncertainty"} <= names
    # Points should sum (approximately) to the final score.
    assert abs(sum(f["points"] for f in risk["factors"]) - risk["risk_score"]) < 0.5
