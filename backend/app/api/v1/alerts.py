import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.alert import AlertCreate, AlertEventOut, AlertOut, AlertUpdate
from app.services import alert_service
from app.services.market_data.base import InvalidTickerError

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    return alert_service.list_alerts(db, user.id)


@router.post("", response_model=AlertOut, status_code=201)
def create_alert(
    body: AlertCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    try:
        return alert_service.create_alert(db, user.id, body.ticker, body.alert_type, body.threshold)
    except InvalidTickerError:
        raise HTTPException(status_code=422, detail=f"Invalid ticker: {body.ticker}") from None


@router.get("/events", response_model=list[AlertEventOut])
def list_events(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return alert_service.list_events(db, user.id, limit)


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: uuid.UUID,
    body: AlertUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = alert_service.update_alert(
        db, user.id, alert_id, threshold=body.threshold, active=body.active
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result


@router.delete("/{alert_id}", status_code=204)
def delete_alert(
    alert_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not alert_service.delete_alert(db, user.id, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
