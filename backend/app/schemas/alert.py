from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AlertType = Literal["price_above", "price_below", "pct_change_above", "risk_above"]


class AlertCreate(BaseModel):
    # Ownership is taken from the bearer token, never from the body. Forbidding
    # extras makes an attempt to pass `user_id` a 422 instead of a no-op.
    model_config = ConfigDict(extra="forbid")

    ticker: str
    alert_type: AlertType
    threshold: float


class AlertUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    threshold: float | None = None
    active: bool | None = None


class AlertOut(BaseModel):
    id: str
    ticker: str
    alert_type: str
    threshold: float
    active: bool
    last_triggered_at: str | None = None
    created_at: str | None = None


class AlertEventOut(BaseModel):
    id: str
    alert_id: str
    ticker: str
    alert_type: str
    triggered_at: str | None = None
    payload: dict = Field(default_factory=dict)
