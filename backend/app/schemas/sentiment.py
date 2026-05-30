from pydantic import BaseModel


class SentimentItem(BaseModel):
    title: str
    publisher: str | None = None
    url: str | None = None
    published_at: str | None = None
    label: str  # positive / negative / neutral
    score: float


class SentimentCounts(BaseModel):
    positive: int
    negative: int
    neutral: int


class SentimentOut(BaseModel):
    ticker: str
    overall_label: str  # positive / negative / neutral / mixed
    overall_score: float  # -1..1
    headline_count: int
    counts: SentimentCounts
    summary: str
    items: list[SentimentItem]
    note: str
