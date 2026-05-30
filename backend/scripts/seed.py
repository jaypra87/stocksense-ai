"""Seed a working demo: a demo user, warmed tickers, a trained model, and a
sample watchlist + alert.

Usage (from backend/, venv active):
    MARKET_DATA_PROVIDER=fake python scripts/seed.py

Idempotent: safe to run repeatedly.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging import configure_logging  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.ml.training import train_and_register  # noqa: E402
from app.services import (  # noqa: E402
    alert_service,
    auth_service,
    indicator_service,
    stock_service,
    watchlist_service,
)
from app.services.auth_service import EmailTakenError  # noqa: E402
from app.services.market_data.registry import get_provider  # noqa: E402

DEMO_EMAIL = "demo@stocksense.ai"
DEMO_PASSWORD = "demopassword123"
TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA"]


def main() -> None:
    configure_logging()
    db = SessionLocal()
    provider = get_provider()

    try:
        # 1) Demo user
        try:
            user = auth_service.signup(db, DEMO_EMAIL, DEMO_PASSWORD)
            print(f"created demo user: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        except EmailTakenError:
            user = auth_service.authenticate(db, DEMO_EMAIL, DEMO_PASSWORD)
            print(f"demo user already exists: {DEMO_EMAIL}")

        # 2) Warm tickers (candles + indicators so the dashboard has data)
        for ticker in TICKERS:
            stock_service.fetch_and_store_candles(db, provider, ticker, "1y", "1d")
            indicator_service.get_indicators(db, provider, ticker, "6m")
            print(f"warmed {ticker}")

        # 3) Train baseline models
        version = "seed-" + datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        summary = train_and_register(db, provider, version=version, tickers=TICKERS)
        print(f"trained model version: {summary['version']}")

        # 4) Sample watchlist + alert
        for ticker in ("NVDA", "AAPL"):
            watchlist_service.add(db, user.id, ticker)
        alert_service.create_alert(db, user.id, "NVDA", "price_above", 10)
        print("seeded watchlist (NVDA, AAPL) + 1 alert")

        print("\nSeed complete. Log in with the demo credentials above.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
