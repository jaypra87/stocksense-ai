"""The tools Stock-man can call. Each wraps an existing service and returns a
compact dict; the agent serialises it for the model and the UI shows it as
the source of the numbers in the answer.

Outputs are trimmed on purpose. The model pays for every token it reads, and
the raw service responses carry series data and chart points it never needs.
"""

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.portfolio import Position
from app.ml.backtest import NotEnoughDataError
from app.ml.features import HORIZON_DAYS
from app.ml.registry import ModelNotReadyError, NoModelError
from app.services import (
    backtest_service,
    indicator_service,
    portfolio_service,
    prediction_service,
    risk_service,
    sentiment_service,
    stock_service,
    watchlist_service,
)
from app.services.market_data.base import InvalidTickerError, MarketDataProvider, ProviderError

logger = logging.getLogger(__name__)

HORIZONS = list(HORIZON_DAYS)


@dataclass
class ToolContext:
    db: Session
    redis: Redis
    provider: MarketDataProvider
    user_id: uuid.UUID


class ToolError(Exception):
    """A tool could not produce a result. The message goes back to the model
    so it can tell the user, so it must be safe and specific."""


def _ticker(props: dict | None = None) -> dict:
    return {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Ticker symbol, e.g. AAPL, BRK-B or VFV.TO.",
            },
            **(props or {}),
        },
        "required": ["ticker", *((props or {}).keys())],
        "additionalProperties": False,
    }


_HORIZON = {
    "horizon": {
        "type": "string",
        "enum": HORIZONS,
        "description": "Forecast horizon.",
    }
}

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_quote",
        "description": "Latest price snapshot for a ticker: price, day change, day and "
        "52-week range, volume and market cap. Quotes may be delayed.",
        "input_schema": _ticker(),
        "strict": True,
    },
    {
        "name": "get_forecast",
        "description": "The app's ML trend forecast for a ticker over 1d, 7d or 30d: "
        "direction, confidence, expected price range, the factors behind it and the "
        "risk score. Probabilistic and frequently wrong; say so.",
        "input_schema": _ticker(_HORIZON),
        "strict": True,
    },
    {
        "name": "get_risk",
        "description": "Composite 0-100 risk score for a ticker with its factor "
        "breakdown (volatility, drawdown, volume, trend, model uncertainty, sentiment).",
        "input_schema": _ticker(),
        "strict": True,
    },
    {
        "name": "get_sentiment",
        "description": "News sentiment for a ticker from recent headlines: overall "
        "label and score, counts, a summary and the top headlines.",
        "input_schema": _ticker(),
        "strict": True,
    },
    {
        "name": "get_indicators",
        "description": "Latest technical indicators for a ticker (RSI, MACD, moving "
        "averages, Bollinger position, 30-day volatility, drawdown) plus derived signals.",
        "input_schema": _ticker(),
        "strict": True,
    },
    {
        "name": "run_backtest",
        "description": "Walk-forward backtest of the forecast model on a ticker: "
        "directional accuracy against naive baselines and whether it beat them. Slow; "
        "use only when the user asks how good the model is.",
        "input_schema": _ticker(_HORIZON),
        "strict": True,
    },
    {
        "name": "get_portfolio",
        "description": "The user's paper portfolio: cash, equity, total and day P&L, "
        "and each position's size, cost, price, value, return and weight.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
    {
        "name": "get_watchlist",
        "description": "Tickers the user has saved to their watchlist.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
    {
        "name": "propose_paper_trade",
        "description": "Draft a paper trade for the user to review in the trade ticket. "
        "Nothing is executed. Use only when the user asks for a trade idea, size it "
        "in shares or in dollars (one, not both), and give a one-sentence rationale "
        "grounded in tool results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "side": {"type": "string", "enum": ["buy", "sell"]},
                "quantity": {"type": ["number", "null"], "description": "Shares, or null."},
                "amount": {"type": ["number", "null"], "description": "Dollars, or null."},
                "rationale": {"type": "string"},
            },
            "required": ["ticker", "side", "quantity", "amount", "rationale"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def run(ctx: ToolContext, name: str, args: dict) -> dict:
    handler = _HANDLERS.get(name)
    if handler is None:
        raise ToolError(f"Unknown tool: {name}")
    try:
        return handler(ctx, args)
    except InvalidTickerError:
        raise ToolError(f"Unknown ticker: {args.get('ticker', '?')}") from None
    except ProviderError as exc:
        logger.warning("stockman tool %s: provider error: %s", name, exc)
        raise ToolError("The market data provider is unavailable right now.") from None
    except (ModelNotReadyError, NoModelError):
        raise ToolError("The forecast model is not loaded yet. Try again in a minute.") from None
    except NotEnoughDataError as exc:
        raise ToolError(f"Not enough price history to backtest: {exc}") from None
    except ToolError:
        raise
    except Exception:
        logger.exception("stockman tool %s failed", name)
        raise ToolError("That tool failed unexpectedly.") from None


def _quote(ctx: ToolContext, args: dict) -> dict:
    q = stock_service.get_quote(ctx.redis, ctx.provider, args["ticker"])
    keys = (
        "ticker", "price", "previous_close", "change", "change_percent", "open",
        "day_high", "day_low", "volume", "market_cap", "fifty_two_week_high",
        "fifty_two_week_low", "currency", "exchange", "as_of",
    )  # fmt: skip
    return {k: q.get(k) for k in keys}


def _forecast(ctx: ToolContext, args: dict) -> dict:
    p = prediction_service.predict(ctx.db, ctx.redis, ctx.provider, args["ticker"], args["horizon"])
    return {
        "ticker": p["ticker"],
        "horizon": p["horizon"],
        "trend": p["trend"],
        "confidence": p["confidence"],
        "class_probabilities": p["class_probabilities"],
        "last_close": p["last_close"],
        "expected_low": p["expected_low"],
        "expected_high": p["expected_high"],
        "risk_score": p["risk_score"],
        "risk_level": p["risk_level"],
        "factors": [f["description"] for f in p["top_factors"]],
        "notes": p["notes"],
        "model_version": p["model_version"],
    }


def _risk(ctx: ToolContext, args: dict) -> dict:
    r = risk_service.get_risk(ctx.db, ctx.redis, ctx.provider, args["ticker"])
    return {
        "ticker": r["ticker"],
        "risk_score": r["risk_score"],
        "risk_level": r["risk_level"],
        "factors": [
            {"name": f["name"], "score": f["score"], "description": f["description"]}
            for f in r["factors"]
        ],
        "as_of": r["as_of"],
    }


def _sentiment(ctx: ToolContext, args: dict) -> dict:
    s = sentiment_service.get_sentiment(ctx.db, ctx.redis, ctx.provider, args["ticker"])
    return {
        "ticker": s["ticker"],
        "overall_label": s["overall_label"],
        "overall_score": s["overall_score"],
        "headline_count": s["headline_count"],
        "counts": s["counts"],
        "summary": s["summary"],
        "headlines": [
            {
                "title": i["title"],
                "publisher": i["publisher"],
                "label": i["label"],
                "published_at": i["published_at"],
            }
            for i in s["items"][:5]
        ],
    }


def _indicators(ctx: ToolContext, args: dict) -> dict:
    ind = indicator_service.get_indicators(ctx.db, ctx.provider, args["ticker"], "6m")
    latest = ind["latest"]
    keys = (
        "timestamp", "close", "sma_7", "sma_30", "sma_100", "ema_20", "rsi_14", "macd",
        "macd_signal", "bollinger_upper", "bollinger_lower", "volatility_30", "drawdown",
        "max_drawdown", "relative_volume",
    )  # fmt: skip
    return {
        "ticker": ind["ticker"],
        "latest": {k: latest.get(k) for k in keys},
        "signals": ind["signals"],
    }


def _backtest(ctx: ToolContext, args: dict) -> dict:
    bt = backtest_service.run_backtest(
        ctx.db, ctx.provider, ctx.user_id, args["ticker"], args["horizon"]
    )
    return {
        "ticker": bt["ticker"],
        "horizon": bt["horizon"],
        "start_date": bt["start_date"],
        "end_date": bt["end_date"],
        "metrics": bt["metrics"],
        "note": bt["note"],
    }


def _portfolio(ctx: ToolContext, args: dict) -> dict:
    s = portfolio_service.summary(ctx.db, ctx.redis, ctx.provider, ctx.user_id)
    keys = (
        "ticker", "quantity", "avg_cost", "price", "market_value", "unrealized_pnl",
        "unrealized_pnl_pct", "day_change", "weight",
    )  # fmt: skip
    return {
        "cash": s["cash"],
        "starting_cash": s["starting_cash"],
        "equity": s["equity"],
        "market_value": s["market_value"],
        "unrealized_pnl": s["unrealized_pnl"],
        "realized_pnl": s["realized_pnl"],
        "total_return": s["total_return"],
        "total_return_pct": s["total_return_pct"],
        "day_change": s["day_change"],
        "day_change_pct": s["day_change_pct"],
        "positions": [{k: p[k] for k in keys} for p in s["positions"]],
        "as_of": s["as_of"],
    }


def _watchlist(ctx: ToolContext, args: dict) -> dict:
    items = watchlist_service.list_watchlist(ctx.db, ctx.user_id)
    return {"tickers": [{"ticker": i["ticker"], "company_name": i["company_name"]} for i in items]}


def _propose_trade(ctx: ToolContext, args: dict) -> dict:
    quantity, amount = args.get("quantity"), args.get("amount")
    if (quantity is None) == (amount is None):
        raise ToolError("Size the trade in shares or in dollars, not both and not neither.")
    quote = stock_service.get_quote(ctx.redis, ctx.provider, args["ticker"])
    ticker = quote["ticker"]
    price = Decimal(str(quote["price"]))
    shares = Decimal(str(quantity)) if quantity is not None else Decimal(str(amount)) / price
    shares = shares.quantize(Decimal("0.000001"))
    if shares <= 0:
        raise ToolError("The trade size must be positive.")

    portfolio = portfolio_service.get_or_create(ctx.db, ctx.user_id)
    held = ctx.db.execute(
        select(Position.quantity).where(
            Position.portfolio_id == portfolio.id, Position.ticker == ticker
        )
    ).scalar_one_or_none() or Decimal(0)

    return {
        "proposal": True,
        "ticker": ticker,
        "side": args["side"],
        "quantity": float(shares),
        "estimated_price": float(price),
        "estimated_total": float((shares * price).quantize(Decimal("0.01"))),
        "cash_available": float(portfolio.cash),
        "currently_held": float(held),
        "rationale": args["rationale"],
        "status": "Not executed. The user reviews and confirms it in the trade ticket.",
    }


_HANDLERS: dict[str, Callable[[ToolContext, dict], dict]] = {
    "get_quote": _quote,
    "get_forecast": _forecast,
    "get_risk": _risk,
    "get_sentiment": _sentiment,
    "get_indicators": _indicators,
    "run_backtest": _backtest,
    "get_portfolio": _portfolio,
    "get_watchlist": _watchlist,
    "propose_paper_trade": _propose_trade,
}
