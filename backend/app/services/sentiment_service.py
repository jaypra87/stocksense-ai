"""Orchestrates sentiment: fetch news -> classify -> summarize -> persist -> return.

Cached in Redis (15 min) so we don't hammer the news source. A snapshot is
persisted on each cache miss, building sentiment history over time.
"""

from redis import Redis
from sqlalchemy.orm import Session

from app.cache.cache import cached_json
from app.cache.keys import TTL_SENTIMENT, sentiment_key
from app.db.models.sentiment_snapshot import SentimentSnapshot
from app.services import sentiment, stock_service
from app.services.market_data.base import MarketDataProvider

NOTE = "Sentiment is derived from recent headlines for context only. Not financial advice."


def get_sentiment(
    db: Session, redis: Redis, provider: MarketDataProvider, raw_ticker: str
) -> dict:
    ticker = stock_service.normalize_ticker(raw_ticker)

    def produce() -> dict:
        news = provider.get_news(ticker)
        titles = [n.title for n in news]
        analysis = sentiment.analyze(titles)
        summary = sentiment.build_summary(ticker, analysis, len(titles))

        items = [
            {
                "title": n.title,
                "publisher": n.publisher,
                "url": n.url,
                "published_at": n.published_at.isoformat() if n.published_at else None,
                "label": analysis["labels"][i],
                "score": analysis["scores"][i],
            }
            for i, n in enumerate(news)
        ]

        result = {
            "ticker": ticker,
            "overall_label": analysis["overall_label"],
            "overall_score": analysis["overall_score"],
            "headline_count": len(titles),
            "counts": analysis["counts"],
            "summary": summary,
            "items": items,
            "note": NOTE,
        }
        _store(db, result)
        return result

    return cached_json(redis, sentiment_key(ticker), TTL_SENTIMENT, produce)


def sentiment_score(
    db: Session, redis: Redis, provider: MarketDataProvider, ticker: str
) -> float | None:
    """Best-effort overall score for the risk engine. Never raises."""
    try:
        return get_sentiment(db, redis, provider, ticker)["overall_score"]
    except Exception:  # noqa: BLE001 — sentiment must never break a risk/prediction call
        return None


def _store(db: Session, result: dict) -> None:
    db.add(
        SentimentSnapshot(
            ticker=result["ticker"],
            sentiment_label=result["overall_label"],
            sentiment_score=result["overall_score"],
            headline_count=result["headline_count"],
            summary=result["summary"],
            source_json={"items": result["items"], "counts": result["counts"]},
        )
    )
    db.commit()
