"""yfinance-backed provider. Good for development — no API key required.

yfinance scrapes Yahoo Finance, so calls can be slow or rate-limited. The cache
layer above this (see stock_service) is what protects us from hammering it.

Not all Yahoo endpoints are equally available. The chart endpoint behind
`Ticker.history()` is public, but `fast_info`, `info`, `news` and `Search` go
through the crumb/cookie-authenticated API, which Yahoo routinely refuses from
datacenter IPs — so on a cloud host the first group keeps working while the
second fails. That asymmetry is why the calls below fall back to candles
wherever a value can be derived from them: a blocked quote endpoint should cost
us freshness and a few extra fields, not the whole page.
"""

import logging
from datetime import UTC, datetime

import yfinance as yf

from app.services.market_data.base import (
    CandleDTO,
    InvalidTickerError,
    MarketDataProvider,
    MetadataDTO,
    NewsItemDTO,
    ProviderError,
    QuoteDTO,
    SearchResultDTO,
)
from app.services.market_data.symbols import search_offline

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    name = "yfinance"

    def search(self, query: str, limit: int = 10) -> list[SearchResultDTO]:
        try:
            results = yf.Search(query, max_results=limit).quotes
        except Exception as exc:  # noqa: BLE001 — vendor lib raises bare Exceptions
            logger.warning("yfinance search failed for %r: %s", query, exc)
            results = []

        out: list[SearchResultDTO] = []
        for r in results:
            symbol = r.get("symbol")
            if not symbol:
                continue
            out.append(
                SearchResultDTO(
                    symbol=symbol,
                    name=r.get("longname") or r.get("shortname"),
                    exchange=r.get("exchange"),
                    type=r.get("quoteType"),
                )
            )

        if not out:
            # Upstream search refused us (or genuinely knows nothing). Fall back
            # to the offline index so a name query like "google" still resolves.
            out = [SearchResultDTO(**r) for r in search_offline(query, limit)]
        return out

    def get_quote(self, ticker: str) -> QuoteDTO:
        try:
            fi = yf.Ticker(ticker).fast_info
            last = fi.get("lastPrice") if isinstance(fi, dict) else fi.last_price
        except Exception as exc:  # noqa: BLE001
            logger.warning("fast_info failed for %s (%s); deriving from candles", ticker, exc)
            return self._quote_from_candles(ticker)

        if last is None:
            return self._quote_from_candles(ticker)

        def g(attr: str) -> float | None:
            try:
                return getattr(fi, attr)
            except Exception:  # noqa: BLE001
                return None

        prev = g("previous_close")
        change = (last - prev) if (last is not None and prev) else None
        change_pct = (change / prev * 100) if (change is not None and prev) else None

        return QuoteDTO(
            ticker=ticker,
            price=float(last),
            previous_close=prev,
            change=change,
            change_percent=change_pct,
            open=g("open"),
            day_high=g("day_high"),
            day_low=g("day_low"),
            volume=g("last_volume"),
            market_cap=g("market_cap"),
            fifty_two_week_high=g("year_high"),
            fifty_two_week_low=g("year_low"),
            currency=g("currency"),
            exchange=g("exchange"),
            as_of=datetime.now(UTC),
        )

    def get_candles(self, ticker: str, period: str, interval: str) -> list[CandleDTO]:
        try:
            df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"history fetch failed for {ticker}: {exc}") from exc

        if df.empty:
            return []

        candles: list[CandleDTO] = []
        for ts, row in df.iterrows():
            candles.append(
                CandleDTO(
                    timestamp=ts.to_pydatetime().astimezone(UTC),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    adj_close=float(row["Adj Close"]) if "Adj Close" in row else None,
                    volume=int(row["Volume"]) if not _is_nan(row["Volume"]) else None,
                )
            )
        return candles

    def get_metadata(self, ticker: str) -> MetadataDTO:
        try:
            info = yf.Ticker(ticker).info
        except Exception as exc:  # noqa: BLE001
            logger.warning("info failed for %s (%s); falling back to bare metadata", ticker, exc)
            info = {}

        if not info or info.get("symbol") is None and info.get("shortName") is None:
            # We can't tell "blocked" from "no such ticker" by the error alone, so
            # ask the endpoint that still works: if the symbol has candles it is
            # real, and a name-less profile beats failing the whole page.
            if self._has_candles(ticker):
                return MetadataDTO(ticker=ticker)
            raise InvalidTickerError(ticker)

        return MetadataDTO(
            ticker=ticker,
            company_name=info.get("longName") or info.get("shortName"),
            exchange=info.get("fullExchangeName") or info.get("exchange"),
            sector=info.get("sector"),
            currency=info.get("currency"),
            extra={
                "industry": info.get("industry"),
                "website": info.get("website"),
                "summary": info.get("longBusinessSummary"),
                "market_cap": info.get("marketCap"),
            },
        )


    # --- candle-derived fallbacks -------------------------------------------
    # These exist so a refused quote/profile endpoint degrades to "yesterday's
    # official close" instead of an error page. Anything the chart endpoint
    # can't tell us (market cap, 52-week range, live intraday price) is left
    # None, which every consumer already handles.

    def _recent_daily_candles(self, ticker: str) -> list[CandleDTO]:
        """Last few daily bars, or [] if even the chart endpoint is unavailable."""
        try:
            return self.get_candles(ticker, period="1mo", interval="1d")
        except ProviderError as exc:
            logger.warning("candle fallback failed for %s: %s", ticker, exc)
            return []

    def _has_candles(self, ticker: str) -> bool:
        return bool(self._recent_daily_candles(ticker))

    def _quote_from_candles(self, ticker: str) -> QuoteDTO:
        """Build a quote from the most recent daily bar.

        `as_of` is the bar's own timestamp, not now(): the price is a close, and
        stamping it with the current time would misrepresent a stale figure as
        live. Callers surface that timestamp, so the staleness stays visible.
        """
        candles = self._recent_daily_candles(ticker)
        if not candles:
            # Neither the quote endpoint nor the chart endpoint knows this
            # symbol — at that point "invalid ticker" is the honest answer.
            raise InvalidTickerError(ticker)

        latest = candles[-1]
        prev = candles[-2].close if len(candles) > 1 else None
        change = (latest.close - prev) if prev else None
        change_pct = (change / prev * 100) if (change is not None and prev) else None

        window = candles[-252:]
        return QuoteDTO(
            ticker=ticker,
            price=latest.close,
            previous_close=prev,
            change=change,
            change_percent=change_pct,
            open=latest.open,
            day_high=latest.high,
            day_low=latest.low,
            volume=latest.volume,
            market_cap=None,
            fifty_two_week_high=max(c.high for c in window),
            fifty_two_week_low=min(c.low for c in window),
            currency=None,
            exchange=None,
            as_of=latest.timestamp,
        )

    def get_news(self, ticker: str, limit: int = 10) -> list[NewsItemDTO]:
        try:
            raw = yf.Ticker(ticker).news or []
        except Exception as exc:  # noqa: BLE001
            logger.warning("yfinance news failed for %s: %s", ticker, exc)
            return []

        items: list[NewsItemDTO] = []
        for entry in raw[:limit]:
            # yfinance 1.x nests fields under "content"; older versions are flat.
            c = entry.get("content", entry)
            title = c.get("title")
            if not title:
                continue
            provider = c.get("provider") or {}
            url = (c.get("canonicalUrl") or {}).get("url") or c.get("link")
            items.append(
                NewsItemDTO(
                    title=title,
                    publisher=provider.get("displayName") if isinstance(provider, dict)
                    else c.get("publisher"),
                    url=url,
                    published_at=_parse_news_time(c),
                    summary=c.get("summary"),
                )
            )
        return items


def _parse_news_time(content: dict) -> datetime | None:
    pub = content.get("pubDate") or content.get("displayTime")
    if isinstance(pub, str):
        try:
            return datetime.fromisoformat(pub.replace("Z", "+00:00"))
        except ValueError:
            return None
    epoch = content.get("providerPublishTime")
    if isinstance(epoch, int | float):
        return datetime.fromtimestamp(epoch, tz=UTC)
    return None


def _is_nan(value: object) -> bool:
    return value != value  # NaN is the only value not equal to itself
