from pydantic import BaseModel

from app.schemas.risk import RiskFactor


class TopFactor(BaseModel):
    feature: str
    value: float
    importance: float
    contribution: float | None = None  # signed per-prediction attribution
    direction: str | None = None  # elevated / depressed vs training norm
    description: str


class PredictionOut(BaseModel):
    ticker: str
    horizon: str
    trend: str
    confidence: float
    expected_return_low: float | None = None
    expected_return_high: float | None = None
    expected_low: float | None = None
    expected_high: float | None = None
    last_close: float | None = None
    risk_score: float | None = None
    risk_level: str | None = None
    risk_factors: list[RiskFactor] = []
    model_version: str
    class_probabilities: dict[str, float]
    top_factors: list[TopFactor]
    notes: str
    disclaimer: str


class PredictionHistoryItem(BaseModel):
    id: str
    ticker: str
    horizon: str
    trend: str
    confidence: float
    expected_low: float | None = None
    expected_high: float | None = None
    model_version: str
    created_at: str | None = None
