"""Cloudflare Turnstile verification.

Turnstile is the challenge behind "add bot protection": the browser runs a
mostly-invisible check and hands back a short-lived token, which the API
confirms with Cloudflare before honouring the request. It guards the places
where an automated client would otherwise get something for nothing: saving
or signing in to an account, and minting more guest sessions than the per-IP
allowance after the plain limit has tripped.

Disabled when no secret is configured (development, or a deployment that has
not set it up yet). Production logs that loudly at boot; it does not refuse to
run, because the rate limits still stand and a missing CAPTCHA should degrade
to "less protected", not "down".
"""

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger("stocksense.turnstile")

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile(token: str | None, remote_ip: str | None = None) -> bool:
    """True if the token is valid, or if Turnstile is not configured."""
    settings = get_settings()
    if not settings.turnstile_enabled:
        return True
    if not token:
        return False
    data = {"secret": settings.turnstile_secret_key, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    try:
        resp = httpx.post(VERIFY_URL, data=data, timeout=5.0)
        resp.raise_for_status()
        body = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        # Cloudflare unreachable: fail closed for the auth flows this guards.
        # They are rare, user-initiated actions; a retry costs the user a click.
        logger.warning("Turnstile verification unavailable: %s", exc)
        return False
    ok = bool(body.get("success"))
    if not ok:
        logger.info("Turnstile rejected a token: %s", body.get("error-codes"))
    return ok
