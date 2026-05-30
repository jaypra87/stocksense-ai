"""Deploy-safe, idempotent startup bootstrap.

Differs from seed.py: this is designed to run on *every* container start, so it
never duplicates data. It ensures a demo user, warms a few tickers, and trains a
model only when there isn't a usable one (e.g. a fresh container whose ephemeral
disk lost the joblib artifact, even though the DB row survived).
"""

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.logging import configure_logging  # noqa: E402
from app.db.models.model_artifact import ModelArtifact  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.ml.training import train_and_register  # noqa: E402
from app.services import (  # noqa: E402
    auth_service,
    indicator_service,
    stock_service,
    watchlist_service,
)
from app.services.auth_service import EmailTakenError  # noqa: E402
from app.services.market_data.registry import get_provider  # noqa: E402

log = logging.getLogger("bootstrap")

DEMO_EMAIL = "demo@stocksense.ai"
DEMO_PASSWORD = "demopassword123"
TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA"]


def _has_usable_model(db) -> bool:
    """An active model exists AND its artifact file is present on disk."""
    active = db.execute(
        select(ModelArtifact).where(ModelArtifact.is_active.is_(True))
    ).scalars().all()
    return bool(active) and all(Path(a.path).exists() for a in active)


def main() -> None:
    configure_logging()
    db = SessionLocal()
    provider = get_provider()
    try:
        # Demo user (idempotent).
        try:
            auth_service.signup(db, DEMO_EMAIL, DEMO_PASSWORD)
            log.info("created demo user")
        except EmailTakenError:
            log.info("demo user already exists")
        user = auth_service.authenticate(db, DEMO_EMAIL, DEMO_PASSWORD)

        # Warm tickers so the dashboard has data immediately.
        for ticker in TICKERS:
            try:
                stock_service.fetch_and_store_candles(db, provider, ticker, "1y", "1d")
                indicator_service.get_indicators(db, provider, ticker, "6m")
                log.info("warmed %s", ticker)
            except Exception as exc:  # noqa: BLE001 — warming is best-effort
                log.warning("warm %s failed: %s", ticker, exc)

        # Train only when there's no usable model (avoids piling up versions).
        if _has_usable_model(db):
            log.info("usable active model present; skipping training")
        else:
            version = "boot-" + datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            train_and_register(db, provider, version=version, tickers=TICKERS)
            log.info("trained model %s", version)

        # Sample watchlist (idempotent — on-conflict-do-nothing).
        for ticker in ("NVDA", "AAPL"):
            try:
                watchlist_service.add(db, user.id, ticker)
            except Exception as exc:  # noqa: BLE001
                log.warning("watchlist add %s failed: %s", ticker, exc)

        log.info("bootstrap complete")
    finally:
        db.close()


if __name__ == "__main__":
    main()
