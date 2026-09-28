"""A small offline symbol index, used only as a search fallback.

Yahoo's search endpoint is one of the crumb/cookie-authenticated ones, which is
exactly the class of call that gets refused from datacenter IPs. When it is
unavailable the search box would otherwise return nothing at all for a
name-based query like "google" — the app looks broken even though quotes,
charts and indicators are fine.

This is deliberately a short, static list of widely-held symbols: enough to keep
the demo usable when upstream search is down, small enough to stay honest about
what it is. It is never consulted while live search works.
"""

# (symbol, company name, exchange)
_INDEX: list[tuple[str, str, str]] = [
    ("AAPL", "Apple Inc.", "NASDAQ"),
    ("MSFT", "Microsoft Corporation", "NASDAQ"),
    ("GOOGL", "Alphabet Inc. (Google) Class A", "NASDAQ"),
    ("GOOG", "Alphabet Inc. (Google) Class C", "NASDAQ"),
    ("AMZN", "Amazon.com, Inc.", "NASDAQ"),
    ("NVDA", "NVIDIA Corporation", "NASDAQ"),
    ("META", "Meta Platforms, Inc. (Facebook)", "NASDAQ"),
    ("TSLA", "Tesla, Inc.", "NASDAQ"),
    ("BRK-B", "Berkshire Hathaway Inc. Class B", "NYSE"),
    ("JPM", "JPMorgan Chase & Co.", "NYSE"),
    ("V", "Visa Inc.", "NYSE"),
    ("MA", "Mastercard Incorporated", "NYSE"),
    ("UNH", "UnitedHealth Group Incorporated", "NYSE"),
    ("JNJ", "Johnson & Johnson", "NYSE"),
    ("WMT", "Walmart Inc.", "NYSE"),
    ("PG", "Procter & Gamble Company", "NYSE"),
    ("XOM", "Exxon Mobil Corporation", "NYSE"),
    ("HD", "The Home Depot, Inc.", "NYSE"),
    ("KO", "The Coca-Cola Company", "NYSE"),
    ("PEP", "PepsiCo, Inc.", "NASDAQ"),
    ("COST", "Costco Wholesale Corporation", "NASDAQ"),
    ("DIS", "The Walt Disney Company", "NYSE"),
    ("NFLX", "Netflix, Inc.", "NASDAQ"),
    ("ADBE", "Adobe Inc.", "NASDAQ"),
    ("CRM", "Salesforce, Inc.", "NYSE"),
    ("INTC", "Intel Corporation", "NASDAQ"),
    ("AMD", "Advanced Micro Devices, Inc.", "NASDAQ"),
    ("QCOM", "QUALCOMM Incorporated", "NASDAQ"),
    ("ORCL", "Oracle Corporation", "NYSE"),
    ("IBM", "International Business Machines Corporation", "NYSE"),
    ("CSCO", "Cisco Systems, Inc.", "NASDAQ"),
    ("BA", "The Boeing Company", "NYSE"),
    ("NKE", "NIKE, Inc.", "NYSE"),
    ("MCD", "McDonald's Corporation", "NYSE"),
    ("SBUX", "Starbucks Corporation", "NASDAQ"),
    ("PYPL", "PayPal Holdings, Inc.", "NASDAQ"),
    ("UBER", "Uber Technologies, Inc.", "NYSE"),
    ("ABNB", "Airbnb, Inc.", "NASDAQ"),
    ("SHOP", "Shopify Inc.", "NYSE"),
    ("SQ", "Block, Inc. (Square)", "NYSE"),
    ("PLTR", "Palantir Technologies Inc.", "NASDAQ"),
    ("SNOW", "Snowflake Inc.", "NYSE"),
    ("SPY", "SPDR S&P 500 ETF Trust", "NYSEARCA"),
    ("QQQ", "Invesco QQQ Trust", "NASDAQ"),
    ("VOO", "Vanguard S&P 500 ETF", "NYSEARCA"),
    ("VTI", "Vanguard Total Stock Market ETF", "NYSEARCA"),
]

# Extra search terms that don't appear in the official company name.
_ALIASES: dict[str, tuple[str, ...]] = {
    "GOOGL": ("google", "alphabet"),
    "GOOG": ("google", "alphabet"),
    "META": ("facebook", "instagram"),
    "BRK-B": ("berkshire",),
    "SQ": ("square",),
}


def search_offline(query: str, limit: int = 10) -> list[dict]:
    """Substring match over symbol, company name and aliases.

    Exact symbol matches rank first, then prefix matches, then anything else,
    so typing a known ticker still puts it at the top.
    """
    q = query.strip().lower()
    if not q:
        return []

    scored: list[tuple[int, dict]] = []
    for symbol, name, exchange in _INDEX:
        haystacks = (symbol.lower(), name.lower(), *_ALIASES.get(symbol, ()))

        if symbol.lower() == q:
            rank = 0
        elif any(h.startswith(q) for h in haystacks):
            rank = 1
        elif any(q in h for h in haystacks):
            rank = 2
        else:
            continue

        scored.append(
            (rank, {"symbol": symbol, "name": name, "exchange": exchange, "type": "EQUITY"})
        )

    scored.sort(key=lambda pair: (pair[0], pair[1]["symbol"]))
    return [item for _, item in scored[:limit]]
