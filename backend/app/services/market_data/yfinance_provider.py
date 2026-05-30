"""yfinance-backed provider. Good for development — no API key required.

yfinance scrapes Yahoo Finance, so calls can be slow or rate-limited. The cache
layer above this (see stock_service) is what protects us from hammering it.
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

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    name = "yfinance"

    def search(self, query: str, limit: int = 10) -> list[SearchResultDTO]:
        try:
            results = yf.Search(query, max_results=limit).quotes
        except Exception as exc:  # noqa: BLE001 — vendor lib raises bare Exceptions
            logger.warning("yfinance search failed for %r: %s", query, exc)
            return []

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
        return out

    def get_quote(self, ticker: str) -> QuoteDTO:
        try:
            fi = yf.Ticker(ticker).fast_info
            last = fi.get("lastPrice") if isinstance(fi, dict) else fi.last_price
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"quote fetch failed for {ticker}: {exc}") from exc

        if last is None:
            raise InvalidTickerError(ticker)

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
            raise ProviderError(f"metadata fetch failed for {ticker}: {exc}") from exc

        if not info or info.get("symbol") is None and info.get("shortName") is None:
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
