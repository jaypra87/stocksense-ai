"""Deterministic synthetic provider — no network required.

Used for tests and offline development. Same ticker always yields the same data,
so assertions are stable. Selected via MARKET_DATA_PROVIDER=fake.
"""

import random
from datetime import UTC, datetime, timedelta

from app.services.market_data.base import (
    CandleDTO,
    InvalidTickerError,
    MarketDataProvider,
    MetadataDTO,
    NewsItemDTO,
    QuoteDTO,
    SearchResultDTO,
)

# The universe the fake provider "knows about" for search/metadata. Quotes,
# candles, indicators, predictions and backtests are generated synthetically for
# ANY ticker symbol — this list is just what search autocomplete can suggest.
_KNOWN = {
    "AAPL": ("Apple Inc.", "NMS", "Technology"),
    "MSFT": ("Microsoft Corporation", "NMS", "Technology"),
    "NVDA": ("NVIDIA Corporation", "NMS", "Technology"),
    "GOOGL": ("Alphabet Inc.", "NMS", "Communication Services"),
    "AMZN": ("Amazon.com, Inc.", "NMS", "Consumer Cyclical"),
    "META": ("Meta Platforms, Inc.", "NMS", "Communication Services"),
    "TSLA": ("Tesla, Inc.", "NMS", "Consumer Cyclical"),
    "AMD": ("Advanced Micro Devices, Inc.", "NMS", "Technology"),
    "INTC": ("Intel Corporation", "NMS", "Technology"),
    "MU": ("Micron Technology, Inc.", "NMS", "Technology"),
    "AVGO": ("Broadcom Inc.", "NMS", "Technology"),
    "ORCL": ("Oracle Corporation", "NYQ", "Technology"),
    "CRM": ("Salesforce, Inc.", "NYQ", "Technology"),
    "ADBE": ("Adobe Inc.", "NMS", "Technology"),
    "NFLX": ("Netflix, Inc.", "NMS", "Communication Services"),
    "DIS": ("The Walt Disney Company", "NYQ", "Communication Services"),
    "JPM": ("JPMorgan Chase & Co.", "NYQ", "Financial Services"),
    "BAC": ("Bank of America Corporation", "NYQ", "Financial Services"),
    "V": ("Visa Inc.", "NYQ", "Financial Services"),
    "MA": ("Mastercard Incorporated", "NYQ", "Financial Services"),
    "WMT": ("Walmart Inc.", "NYQ", "Consumer Defensive"),
    "COST": ("Costco Wholesale Corporation", "NMS", "Consumer Defensive"),
    "KO": ("The Coca-Cola Company", "NYQ", "Consumer Defensive"),
    "PEP": ("PepsiCo, Inc.", "NMS", "Consumer Defensive"),
    "MCD": ("McDonald's Corporation", "NYQ", "Consumer Cyclical"),
    "NKE": ("NIKE, Inc.", "NYQ", "Consumer Cyclical"),
    "XOM": ("Exxon Mobil Corporation", "NYQ", "Energy"),
    "CVX": ("Chevron Corporation", "NYQ", "Energy"),
    "JNJ": ("Johnson & Johnson", "NYQ", "Healthcare"),
    "PFE": ("Pfizer Inc.", "NYQ", "Healthcare"),
    "UNH": ("UnitedHealth Group Incorporated", "NYQ", "Healthcare"),
    "BA": ("The Boeing Company", "NYQ", "Industrials"),
    "GE": ("General Electric Company", "NYQ", "Industrials"),
    "BRK-B": ("Berkshire Hathaway Inc.", "NYQ", "Financial Services"),
    "SPY": ("SPDR S&P 500 ETF Trust", "PCX", "ETF"),
    "QQQ": ("Invesco QQQ Trust", "NMS", "ETF"),
    "VFV.TO": ("Vanguard S&P 500 Index ETF", "TOR", "ETF"),
}

# Number of DAILY bars per period. Weekly intervals divide by 5 (see get_candles).
_PERIOD_DAYS = {
    "1d": 1,
    "5d": 5,
    "1mo": 22,
    "3mo": 66,
    "6mo": 126,
    "ytd": 100,
    "1y": 252,
    "5y": 1250,  # ~5 years of trading days (weekly view -> 250 bars)
}

# Synthetic headlines spanning positive / negative / neutral tones, so the
# sentiment classifier produces a realistic spread. (template, publisher)
_NEWS_TEMPLATES = [
    ("{t} beats quarterly earnings expectations as revenue surges", "Market Wire"),
    ("Analysts upgrade {t} on strong product demand and growth outlook", "Street Insider"),
    ("{t} hits record high after upbeat guidance", "Finance Daily"),
    ("{t} expands into new markets, boosting optimism", "Global Biz"),
    ("{t} misses revenue targets; shares drop sharply", "Market Wire"),
    ("Regulators open probe into {t} over data practices", "Reg Watch"),
    ("Concerns mount as {t} faces slowing growth and margin pressure", "Finance Daily"),
    ("{t} announces layoffs amid restructuring", "Street Insider"),
    ("{t} unveils new product line at annual event", "Tech Times"),
    ("{t} to report earnings next week, investors await guidance", "Global Biz"),
]


class FakeProvider(MarketDataProvider):
    name = "fake"

    def search(self, query: str, limit: int = 10) -> list[SearchResultDTO]:
        q = query.upper()
        hits = [
            SearchResultDTO(symbol=sym, name=name, exchange=exch, type="EQUITY")
            for sym, (name, exch, _sector) in _KNOWN.items()
            if q in sym or q in name.upper()
        ]
        return hits[:limit]

    def get_candles(self, ticker: str, period: str, interval: str) -> list[CandleDTO]:
        n = _PERIOD_DAYS.get(period, 252)
        if interval == "1wk":
            n = n // 5  # ~5 trading days per week
        rng = random.Random(sum(ord(c) for c in ticker.upper()))
        price = 50 + rng.random() * 200
        # Floor to midnight UTC so repeated calls yield identical timestamps —
        # otherwise the (ticker, interval, timestamp) upsert key never collides
        # and we'd insert duplicate rows instead of updating in place.
        now = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        step = timedelta(weeks=1) if interval == "1wk" else timedelta(days=1)

        candles: list[CandleDTO] = []
        for i in range(n):
            ts = now - step * (n - i)
            drift = rng.uniform(-0.025, 0.027)
            open_ = price
            close = max(1.0, price * (1 + drift))
            high = max(open_, close) * (1 + rng.uniform(0, 0.012))
            low = min(open_, close) * (1 - rng.uniform(0, 0.012))
            candles.append(
                CandleDTO(
                    timestamp=ts,
                    open=round(open_, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    close=round(close, 2),
                    adj_close=round(close, 2),
                    volume=rng.randint(1_000_000, 8_000_000),
                )
            )
            price = close
        return candles

    def get_quote(self, ticker: str) -> QuoteDTO:
        candles = self.get_candles(ticker, "5d", "1d")
        if not candles:
            raise InvalidTickerError(ticker)
        last, prev = candles[-1], candles[-2]
        change = last.close - prev.close
        return QuoteDTO(
            ticker=ticker.upper(),
            price=last.close,
            previous_close=prev.close,
            change=round(change, 2),
            change_percent=round(change / prev.close * 100, 2),
            open=last.open,
            day_high=last.high,
            day_low=last.low,
            volume=last.volume,
            market_cap=last.close * 1_000_000_000,
            fifty_two_week_high=max(c.high for c in candles),
            fifty_two_week_low=min(c.low for c in candles),
            currency="USD",
            exchange=_KNOWN.get(ticker.upper(), (None, "NMS", None))[1],
            as_of=datetime.now(UTC),
        )

    def get_metadata(self, ticker: str) -> MetadataDTO:
        t = ticker.upper()
        name, exch, sector = _KNOWN.get(t, (f"{t} Holdings", "NMS", "Unknown"))
        return MetadataDTO(
            ticker=t,
            company_name=name,
            exchange=exch,
            sector=sector,
            currency="USD",
            extra={"industry": sector, "synthetic": True},
        )

    def get_news(self, ticker: str, limit: int = 10) -> list[NewsItemDTO]:
        t = ticker.upper()
        rng = random.Random(sum(ord(c) for c in t) + 7)
        headlines = _NEWS_TEMPLATES.copy()
        rng.shuffle(headlines)
        # Midnight-floored "now" keeps timestamps deterministic across calls.
        now = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        items: list[NewsItemDTO] = []
        for i, (template, publisher) in enumerate(headlines[:limit]):
            items.append(
                NewsItemDTO(
                    title=template.format(t=t),
                    publisher=publisher,
                    url=f"https://example.com/news/{t.lower()}/{i}",
                    published_at=now - timedelta(days=i),
                    summary=None,
                )
            )
        return items
