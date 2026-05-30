from pydantic import BaseModel


class RiskFactor(BaseModel):
    name: str
    score: float  # 0-100 sub-score
    weight: float
    points: float | None = None  # normalized contribution to the final score
    description: str


class RiskOut(BaseModel):
    ticker: str
    risk_score: float
    risk_level: str  # low / medium / high / very_high
    factors: list[RiskFactor]
    as_of: str
    note: str
