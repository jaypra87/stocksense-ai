from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=2000)


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=120)


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None


class MessageOut(BaseModel):
    id: str
    role: str
    # The model API's content blocks, passed through untouched.
    content: list[dict]
    created_at: str | None = None


class ConversationOut(ConversationSummary):
    messages: list[MessageOut]


class BudgetOut(BaseModel):
    used: int
    limit: int


class StatusOut(BaseModel):
    enabled: bool
    model: str
    budget: BudgetOut
    disclaimer: str


class DigestSource(BaseModel):
    tool: str
    ticker: str | None = None


class DigestOut(BaseModel):
    available: bool
    # Why there is no digest, when `available` is false.
    reason: str | None = None
    for_date: str | None = None
    mode: str | None = None
    body: str | None = None
    sources: list[DigestSource] = []
    grounding: dict = {}
    generated_at: str | None = None
    disclaimer: str
