"""Centralized Redis key builders + TTLs.

Keeping keys in one place avoids typos and accidental collisions, and documents
exactly what we cache and for how long.
"""

# TTLs in seconds
TTL_SEARCH = 60 * 60  # 1 hour — search results change rarely
TTL_QUOTE = 30  # 30 seconds — quotes are "live" but we throttle the provider
TTL_METADATA = 60 * 60 * 24  # 1 day — company metadata is near-static
TTL_SENTIMENT = 15 * 60  # 15 minutes — news refreshes periodically


def search_key(query: str, limit: int) -> str:
    return f"search:{query.lower()}:{limit}"


def quote_key(ticker: str) -> str:
    return f"quote:{ticker.upper()}"


def metadata_key(ticker: str) -> str:
    return f"meta:{ticker.upper()}"


def sentiment_key(ticker: str) -> str:
    return f"sentiment:{ticker.upper()}"
