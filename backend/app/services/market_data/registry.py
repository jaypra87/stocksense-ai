"""Chooses the active provider from settings and exposes it as a dependency."""

from functools import lru_cache

from app.core.config import get_settings
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.fake_provider import FakeProvider
from app.services.market_data.yfinance_provider import YFinanceProvider

_PROVIDERS: dict[str, type[MarketDataProvider]] = {
    "yfinance": YFinanceProvider,
    "fake": FakeProvider,
}


@lru_cache
def get_provider() -> MarketDataProvider:
    """FastAPI dependency: returns the configured provider as a singleton."""
    settings = get_settings()
    provider_cls = _PROVIDERS.get(settings.market_data_provider, YFinanceProvider)
    return provider_cls()
