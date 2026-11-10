"""Work out which address a request really came from.

The app never sees the client socket: in production the chain is

    browser → Vercel (frontend + API proxy) → Render load balancer → uvicorn

Every hop can add to X-Forwarded-For, and the *leftmost* value is whatever the
client chose to send, so trusting it would let anyone pick their own
rate-limit bucket. Trust is therefore anchored on something a client cannot
forge:

1. The frontend proxy sends `X-Proxy-Secret` plus `X-Client-IP`. Vercel
   overwrites X-Forwarded-For with the real client address before the proxy
   ever runs, so when the secret matches, that header is authoritative.
2. Otherwise the request hit the platform directly, and the only address we
   can vouch for is the one the platform's own balancer appended: the
   rightmost X-Forwarded-For entry.
3. With no proxy at all (local dev, tests) it is the socket peer.
"""

import hmac

from fastapi import Request

from app.core.config import get_settings


def client_ip(request: Request) -> str:
    settings = get_settings()

    secret = settings.proxy_shared_secret
    supplied = request.headers.get("x-proxy-secret")
    if secret and supplied and hmac.compare_digest(secret, supplied):
        proxied = request.headers.get("x-client-ip", "").strip()
        if proxied:
            return proxied

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()

    return request.client.host if request.client else "unknown"


def via_trusted_proxy(request: Request) -> bool:
    secret = get_settings().proxy_shared_secret
    supplied = request.headers.get("x-proxy-secret")
    return bool(secret and supplied and hmac.compare_digest(secret, supplied))
