"""StockSense as an MCP server.

The same nine tools Stock-man calls are exposed over the Model Context
Protocol at /mcp, so Claude Desktop, Claude Code or any other MCP client
can ask about a stock or the user's paper portfolio and get the same
grounded numbers. Nothing here can trade: `propose_paper_trade` drafts, and
the person confirms in the app.

Authentication is the app's own session token as a bearer header (minted at
POST /auth/mcp-token), checked the way the API checks it: signed, unexpired,
and naming a live session row. A request with no token gets a 401 before
the protocol layer sees it, and every tool runs under that user's row-level
security context.
"""

import json
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import UTC, datetime

import anyio
import mcp.types as types
from mcp.server.context import ServerRequestContext
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

from app.cache.redis_client import get_redis
from app.core.client_ip import client_ip
from app.core.rate_limit import RateLimiter
from app.core.security import decode_session_token
from app.db.models.session import UserSession
from app.db.session import SessionLocal, set_rls_user
from app.services.market_data.registry import get_provider
from app.services.stockman import tools
from app.services.stockman.tools import ToolContext, ToolError

logger = logging.getLogger("stocksense.mcp")

INSTRUCTIONS = (
    "StockSense AI is an educational stock analytics app. These tools return "
    "live quotes, the app's ML forecasts, risk scores, news sentiment, "
    "technical indicators, backtests and the user's paper portfolio. Forecasts "
    "are probabilistic and often wrong. Nothing here is financial advice, and "
    "no tool can place a trade."
)

_current_user: ContextVar[uuid.UUID] = ContextVar("mcp_user")
# Tool calls run real queries and model inference; the same cap as the chat.
_limiter = RateLimiter("mcp", 120, 300)


async def _list_tools(
    ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(name=t["name"], description=t["description"], input_schema=t["input_schema"])
            for t in tools.TOOL_DEFINITIONS
        ]
    )


async def _call_tool(
    ctx: ServerRequestContext, params: types.CallToolRequestParams
) -> types.CallToolResult:
    user_id = _current_user.get()
    args = params.arguments or {}

    def run() -> dict:
        db = SessionLocal()
        set_rls_user(db, user_id)
        try:
            context = ToolContext(
                db=db, redis=get_redis(), provider=get_provider(), user_id=user_id
            )
            return tools.run(context, params.name, args)
        finally:
            db.close()

    try:
        payload = await anyio.to_thread.run_sync(run)
    except ToolError as exc:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=str(exc))], is_error=True
        )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(payload, default=str))],
        structured_content=payload,
    )


server: Server = Server(
    "stocksense",
    version="0.1.0",
    instructions=INSTRUCTIONS,
    on_list_tools=_list_tools,
    on_call_tool=_call_tool,
)

_manager: StreamableHTTPSessionManager | None = None


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    """Runs the transport for the life of the app. A manager can only be
    started once, so each app start-up gets a fresh one.

    Stateless: every request stands alone, which suits a server behind a
    proxy on a free tier that may restart between calls. DNS-rebinding
    protection is a defence for unauthenticated local servers; here a
    browser cannot attach the bearer token, so the check would only get in
    the way of the proxy.
    """
    global _manager
    _manager = StreamableHTTPSessionManager(
        app=server,
        json_response=True,
        stateless=True,
        security_settings=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    async with _manager.run():
        yield


def _authenticate(token: str) -> uuid.UUID | None:
    decoded = decode_session_token(token)
    if decoded is None:
        return None
    user_id, session_id = decoded
    db = SessionLocal()
    try:
        set_rls_user(db, user_id)
        session = db.get(UserSession, session_id)
        if session is None or session.user_id != user_id:
            return None
        if session.expires_at <= datetime.now(UTC):
            return None
        return user_id
    finally:
        db.close()


class McpEndpoint:
    """ASGI entry for /mcp: bearer auth and a rate limit, then the protocol.

    Registered as a route rather than a mounted sub-app so a bare `/mcp` is
    served directly; a mount would answer it with a redirect to `/mcp/`,
    which not every MCP client follows."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await _handle(scope, receive, send)


async def _handle(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] != "http":
        return
    request = Request(scope, receive)
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    user_id = _authenticate(token.strip()) if scheme.lower() == "bearer" and token else None
    if user_id is None:
        response = JSONResponse(
            {"detail": "A session bearer token is required (POST /api/v1/auth/mcp-token)."},
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )
        await response(scope, receive, send)
        return

    verdict = _limiter.check(get_redis(), client_ip(request))
    if not verdict.allowed:
        response = JSONResponse(
            {"detail": "Too many tool calls. Try again shortly."},
            status_code=429,
            headers={"Retry-After": str(verdict.retry_after)},
        )
        await response(scope, receive, send)
        return

    assert _manager is not None, "MCP transport not started; is the app lifespan running?"
    reset = _current_user.set(user_id)
    try:
        await _manager.handle_request(scope, receive, send)
    finally:
        _current_user.reset(reset)
