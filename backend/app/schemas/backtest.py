from pydantic import BaseModel


class BacktestMetrics(BaseModel):
    n_predictions: int
    directional_accuracy: float
    baseline_accuracy: float
    persistence_accuracy: float
    mae: float
    rmse: float
    baseline_mae: float
    beats_baseline: bool


class BacktestOut(BaseModel):
    id: str
    ticker: str
    horizon: str
    model_version: str
    start_date: str | None = None
    end_date: str | None = None
    status: str
    metrics: BacktestMetrics
    chart_data: dict
    note: str
    disclaimer: str
    created_at: str | None = None


class BacktestSummary(BaseModel):
    id: str
    ticker: str
    horizon: str
    start_date: str | None = None
    end_date: str | None = None
    metrics: BacktestMetrics
    created_at: str | None = None
