# Stock-man

Stock-man is the analyst inside StockSense: a chat panel on every app page, a
full page at `/stock-man`, a daily portfolio digest on the dashboard, and the
same tools exposed to outside assistants over MCP. This records how it is
built and, more to the point, how it is kept honest.

## The rule

**Every number Stock-man states comes from a tool result, and Stock-man never
trades.** Everything below exists to make that true rather than merely asked
for.

## Tools

The model gets nine tools, each a thin wrapper over an existing service
(`app/services/stockman/tools.py`). They return trimmed payloads: the model
pays for every token it reads, and the raw service responses carry chart
series it never needs.

| Tool | Wraps | Notes |
|---|---|---|
| `get_quote` | `stock_service.get_quote` | Delayed quote, day and 52-week range |
| `get_forecast` | `prediction_service.predict` | Trend, confidence, expected range, factors, risk |
| `get_risk` | `risk_service.get_risk` | 0-100 composite with factor breakdown |
| `get_sentiment` | `sentiment_service.get_sentiment` | Label, score, counts, top five headlines |
| `get_indicators` | `indicator_service.get_indicators` | Latest snapshot and derived signals |
| `run_backtest` | `backtest_service.run_backtest` | Walk-forward metrics; the model is told it is slow |
| `get_portfolio` | `portfolio_service.summary` | Cash, equity, P&L, positions |
| `get_watchlist` | `watchlist_service.list_watchlist` | Saved tickers |
| `propose_paper_trade` | quote + portfolio | Prices a draft; **executes nothing** |

Every schema is `strict` with `additionalProperties: false`, so arguments
arrive exactly as declared. Tool failures (unknown ticker, provider down,
model warming up) go back to the model as an error result it can explain,
not as an exception.

## The turn loop

`agent.run_turn` is a hand-written loop rather than the SDK's tool runner
because the UI wants per-token text and per-tool progress, and the last
round has to be forced to answer without tools. Each round is one streamed
model call; tool calls are executed and their results replayed; the loop
ends when the model answers in text or the round cap is hit, at which point
`tool_choice` is set to `none` so it must answer with what it has.

Events stream to the browser as server-sent events: `text_delta`,
`text_reset`, `tool_call`, `tool_result`, `done`, `error`.

Turns are stored as the model API's own content blocks
(`conversation_messages.content`), so a thread replays verbatim and the UI
can show which tool produced which number. A sequence column keeps the
turns of one answer in order; they share a timestamp.

## Grounding

After the model answers, `grounding.check` pulls every figure out of the
text and every number out of the tool results, in the forms a model quotes
them (rounded, and fractions as percentages), and reports what does not
match within a small relative tolerance. Bare integers up to 100, years,
and figures the user typed are not flagged.

An answer with an unmatched figure is retried once: the first answer is
appended to the request, a mid-conversation system message names the
figures and asks for a rewrite using tool results only, and the stream is
reset so the browser replaces the text. Whatever is still unmatched after
that is shown under the answer as a small warning. The superseded answer is
never stored.

This is a check, not a proof. It cannot tell a correct figure from a
correctly-shaped wrong one that happens to appear in some tool result, and it
does not judge words. The eval set covers the words.

## The prompt

The system prompt is frozen text and is the cached prefix; anything that
varies per request belongs in the user turn. It tells the model to call a
tool for every figure, to name the source in plain words, to carry the
models' uncertainty into its wording, never to tell someone what to buy or
sell, to keep answers short, and not to repeat a disclaimer the app already
shows. Trade ideas go through `propose_paper_trade`, which returns a draft
the person reviews in the same trade ticket they would use themselves.

## Spend

Three limits bound the bill on a public demo, all enforced server-side:

| Limit | Default | Where |
|---|---|---|
| Messages per IP | 30 per 5 minutes | `STOCKMAN_RATE_LIMIT` |
| Tokens per user per day | 200,000 | `STOCKMAN_USER_DAILY_TOKENS` |
| Tokens per deployment per day | 4,000,000 | `STOCKMAN_GLOBAL_DAILY_TOKENS` |

Token budgets count what the API reports after each turn, not an estimate
before it, and live in Redis keyed by UTC day. At Haiku 5.5 prices the
global cap is well under a dollar a day. When a budget trips, Stock-man says
it is resting until tomorrow; a dead Redis fails open, because the budget is
cost control, not access control, and the per-IP limit still stands. A
missing API key makes the feature report itself offline; nothing else in
the app depends on it.

Each turn's usage includes `cache_read_input_tokens`. Across turns it should
be non-zero; a zero means the cached prefix is being invalidated somewhere.

## The digest

`GET /stockman/digest` writes the day's digest on the first call and serves
the row after. It gathers the portfolio, each holding's risk score and
headlines, and the 7-day forecast for the three largest positions, then
asks for 120 to 180 words grounded in that bundle. An uninvested account
gets a market digest from its watchlist. A short Redis lock keeps two tabs
from paying twice; the unique `(user, day)` key is the backstop. The day
boundary is UTC.

## MCP

The same nine tools are served at `/mcp` with the streamable HTTP transport,
stateless and JSON-response. Auth is a session bearer token minted at
`POST /auth/mcp-token`, which is a separate session row named "MCP
connector" so it is listed and revocable on its own. Every call runs under
the holder's row-level-security context and the usual per-IP rate limit.
The site proxies `/mcp` on its own origin, so a connector's URL is the site
plus `/mcp`.

To connect Claude Code, mint a token on the settings page and run the
command it shows:

```
claude mcp add --transport http stocksense https://<site>/mcp \
  --header "Authorization: Bearer <token>"
```

## Evals

`evals/stockman/cases.json` holds questions with the properties a good
answer has: which tools must or must not be called, phrases that must or
must not appear, a length cap. `evals/stockman/checks.py` applies them along
with the grounding check and a list of advice phrasings ("you should buy",
"guaranteed") that fail an answer however well grounded it is.

```
cd backend && source .venv/bin/activate
python -m evals.stockman.run        # all cases, a few cents on Haiku
pytest -m live                      # the same cases as a test run
```

The checks themselves are unit-tested with canned transcripts
(`tests/test_stockman_eval_checks.py`), so the bar is tested without a
model. Live runs are opt-in (`-m live`) so an ordinary `pytest` never
spends money.

## Prompt injection

Tool results are data the model reads, and some of it (news headlines) is
written by strangers. The design assumes a headline may try to instruct the
model. What limits the damage is not the prompt but the tool surface:
nothing Stock-man can call moves money, changes an account, or reaches
outside the app, and the only side effect it can produce is a trade draft
the person has to confirm by hand. The grounding check and the eval set
catch the rest of what a hijacked answer would look like.
