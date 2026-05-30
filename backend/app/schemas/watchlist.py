from pydantic import BaseModel


class WatchlistItemOut(BaseModel):
    ticker: str
    company_name: str | None = None
    created_at: str | None = None
