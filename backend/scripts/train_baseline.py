"""Train and register the baseline models.

Usage (from backend/, with venv active):
    python scripts/train_baseline.py
    MARKET_DATA_PROVIDER=fake python scripts/train_baseline.py AAPL MSFT NVDA

Uses the configured market-data provider (MARKET_DATA_PROVIDER env). With
yfinance you get real history; with fake you get deterministic synthetic data
(good for proving the pipeline offline).
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Make `app` importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging import configure_logging  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.ml.training import train_and_register  # noqa: E402
from app.services.market_data.registry import get_provider  # noqa: E402


def main() -> None:
    configure_logging()
    tickers = [t.upper() for t in sys.argv[1:]] or None
    version = "v" + datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    provider = get_provider()
    db = SessionLocal()
    try:
        summary = train_and_register(db, provider, version=version, tickers=tickers)
    finally:
        db.close()

    print(f"\nTrained model version: {summary['version']}")
    print(f"Tickers: {', '.join(summary['tickers'])}")
    for horizon, metrics in summary["horizons"].items():
        clf = metrics["classifier"]
        reg = metrics["regressor"]
        print(
            f"  {horizon:>4}: acc={clf['accuracy']} (baseline {clf['baseline_accuracy']}) "
            f"| MAE={reg['mae']} (baseline {reg['baseline_mae']}) | n_test={metrics['n_test']}"
        )


if __name__ == "__main__":
    main()
