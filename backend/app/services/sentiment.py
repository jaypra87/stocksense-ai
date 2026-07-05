"""Lexicon-based financial sentiment. Pure functions, no model downloads.

Each headline is scored by counting finance-tuned positive/negative terms, with
simple negation handling ("not strong" flips). Scores are in [-1, 1]. This is a
transparent baseline; a future upgrade could swap in FinBERT / an LLM classifier.
"""

import re

_POSITIVE = {
    "beat", "beats", "surge", "surges", "surged", "soar", "soars", "rally", "rallies",
    "gain", "gains", "upgrade", "upgrades", "bullish", "record", "profit", "profits",
    "growth", "strong", "outperform", "jump", "jumps", "rise", "rises", "top", "tops",
    "breakthrough", "optimism", "optimistic", "upbeat", "boost", "boosts", "expands",
    "expansion", "high", "highs", "win", "wins", "approval", "demand", "rebound",
}

_NEGATIVE = {
    "miss", "misses", "missed", "plunge", "plunges", "drop", "drops", "fall", "falls",
    "downgrade", "downgrades", "bearish", "loss", "losses", "weak", "decline", "declines",
    "slump", "cut", "cuts", "lawsuit", "probe", "warning", "warns", "fears", "recall",
    "layoff", "layoffs", "tumble", "tumbles", "sink", "sinks", "crash", "slowing",
    "pressure", "concern", "concerns", "investigation", "fraud", "halt", "delay", "risk",
}

_NEGATIONS = {"not", "no", "never", "without", "fails", "fail", "lacks", "isn't", "wasn't"}

_TOKEN_RE = re.compile(r"[a-z']+")


def score_text(text: str) -> float:
    """Sentiment of a single headline in [-1, 1]."""
    tokens = _TOKEN_RE.findall(text.lower())
    pos = neg = 0
    for i, tok in enumerate(tokens):
        negated = i > 0 and tokens[i - 1] in _NEGATIONS
        if tok in _POSITIVE:
            neg += 1 if negated else 0
            pos += 0 if negated else 1
        elif tok in _NEGATIVE:
            pos += 1 if negated else 0
            neg += 0 if negated else 1
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def label_from_score(score: float) -> str:
    if score > 0.1:
        return "positive"
    if score < -0.1:
        return "negative"
    return "neutral"


def analyze(titles: list[str]) -> dict:
    """Per-headline scores + overall aggregate."""
    scores = [score_text(t) for t in titles]
    labels = [label_from_score(s) for s in scores]
    counts = {
        "positive": labels.count("positive"),
        "negative": labels.count("negative"),
        "neutral": labels.count("neutral"),
    }
    overall_score = round(sum(scores) / len(scores), 4) if scores else 0.0
    return {
        "scores": [round(s, 4) for s in scores],
        "labels": labels,
        "counts": counts,
        "overall_score": overall_score,
        "overall_label": _overall_label(overall_score, counts),
    }


def _overall_label(score: float, counts: dict) -> str:
    # "mixed" when positive and negative coverage are both substantial.
    pos, neg = counts["positive"], counts["negative"]
    if pos and neg and abs(pos - neg) <= 1 and (pos + neg) >= 3:
        return "mixed"
    return label_from_score(score)


def build_summary(ticker: str, analysis: dict, n: int) -> str:
    if n == 0:
        return f"No recent headlines found for {ticker}."
    c = analysis["counts"]
    label = analysis["overall_label"]
    return (
        f"Across {n} recent headlines, coverage of {ticker} is {label} "
        f"(score {analysis['overall_score']:+.2f}): "
        f"{c['positive']} positive, {c['negative']} negative, {c['neutral']} neutral."
    )
