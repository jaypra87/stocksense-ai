# Security posture

StockSense AI is an educational project with a public demo. This records what is
enforced, where the boundaries are, and — just as importantly — what is
deliberately *not* done, so the gaps are known rather than assumed away.

## Checklist

How each item on the project's security checklist is met, and where to look.

| Item | Status | Where |
|---|---|---|
| Hide API keys | Done | No key reaches a browser. The backend address itself is server-side (`BACKEND_URL`); the browser only talks to `/api/v1` on the site's own origin via `frontend/app/api/v1/[...path]/route.ts`. Provider keys live in backend env vars. The only `NEXT_PUBLIC_` values are the demo flag and the Turnstile *site* key, which is public by design. |
| Purge Git secrets | Done | No `.env` has ever been committed (full-history scan clean). `scripts/check-secrets.sh --history` runs in CI on every push; `.gitignore` blocks every `.env*` variant, keys and service-account JSON. |
| Use public DB keys | N/A | There is no client-side database access (this is not a Supabase/Firebase app). The browser never holds a database credential of any kind; the API is the only path to Postgres. |
| Enable row level security | Done | Postgres policies on `users`, `sessions`, `watchlists`, `alerts`, `alert_events`, `backtests` with `FORCE ROW LEVEL SECURITY`; the request's user id is set per transaction (`app/db/session.py`). `tests/test_rls.py`. |
| Encrypt sensitive data | Done | Emails are AES-256-GCM encrypted at the application layer with a keyed hash for lookup (`app/core/crypto.py`); passwords are bcrypt hashes; TLS to Postgres is enforced in production; disks are encrypted by the providers. |
| Enforce server-side auth | Done | Every data router declares `Depends(get_current_user)` at router level. The browser guard is a convenience. `tests/test_access_control.py` fails if a new route ships unclassified. |
| Lock record access | Done | Ownership comes from the session, never the request; services scope every query by `user_id`, and RLS enforces the same at the database. |
| Block field tampering | Done | All request schemas use `extra="forbid"`: an unexpected field (`user_id`, `role`, `id`) is a 422, not a silently ignored key. |
| Secure session cookies | Done | `HttpOnly; Secure; SameSite=Lax; Path=/`, first-party via the proxy. No token in `localStorage`. Sessions are DB rows and revocable (`/auth/logout`, `/auth/logout-all`). |
| Rate limit login | Done | Per-IP fixed windows on login, signup, guest creation, predictions and backtests, in Redis with an in-process fallback when Redis is down (`app/core/rate_limit.py`). Client IP is derived from a source the client cannot spoof (`app/core/client_ip.py`). |
| Add bot protection | Done (needs keys) | Cloudflare Turnstile on sign-in and save-account, and as the challenge when the guest-session limit trips (`app/core/turnstile.py`). Disabled, with a loud warning, until `TURNSTILE_SECRET_KEY` is set. |
| Parameterize queries | Done | All data access goes through SQLAlchemy Core/ORM with bound parameters. The only literal SQL is `SELECT 1` in the health check and the `set_config` calls, which bind their values. |
| Validate all input | Done | Pydantic models with explicit types, lengths and `extra="forbid"` on every body; path/query params typed and bounded; tickers normalised and validated against the provider before use. |
| Escape user content | Done | React escapes all rendered text. The single `dangerouslySetInnerHTML` is static JSON-LD on the landing page with no user input. The API returns JSON only. |
| Restrict file uploads | N/A | The application accepts no file uploads anywhere (no `UploadFile`, no multipart). If one is ever added it needs type/size limits and must not be served back from the same origin. |
| Trim API responses | Done | Every data route declares a `response_model`; nothing beyond the schema leaves the API. `password_hash`, `email_hash` and session ids are never serialised. |
| Add security headers | Done | Both tiers send CSP, HSTS, `X-Frame-Options: DENY`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`; the API also sends `Cache-Control: no-store`. |
| Force HTTPS | Done | Vercel and Render serve HTTPS only and redirect HTTP; HSTS (two years, subdomains) from both; `sslmode=require` to Postgres in production; the session cookie is `Secure`. |
| Scan dependencies | Done | `pip-audit --strict` and `npm audit --audit-level=high` in `.github/workflows/security.yml` on manifest changes and weekly; Dependabot for pip, npm and Actions. |

## Identity and sessions

- **No login wall.** A first visit calls `POST /auth/guest`, which creates a
  guest identity and sets the session cookie. Everything the visitor saves
  belongs to that guest. "Save your account" (`POST /auth/signup` from a guest
  session) upgrades the guest in place, keeping its id and data; signing in from
  a guest browser merges the guest's watchlist, alerts and backtests into the
  account and deletes the guest.
- **Sessions are rows.** The cookie carries a signed token naming a `sessions`
  row; revoking the row ends the session regardless of the token's expiry.
  Sessions last `SESSION_TTL_DAYS` (30). Guests with no live session are purged
  by the bootstrap on each boot (and a daily Celery task where the worker runs).
- Passwords are hashed with **bcrypt** (`BCRYPT_ROUNDS`, 10–15). New passwords
  are capped at 72 bytes because bcrypt ignores the rest. Login compares against
  a dummy hash for unknown emails so timing does not reveal which accounts exist.

## Authorization

- **Server-side, not just in the UI.** Data routers declare
  `Depends(get_current_user)` at *router* level, so a new route inherits it.
- **Ownership is taken from the session, never the request body.**
- **Row-level security** backs the service layer: the request's user id is
  pushed into the transaction (`set_config('app.user_id', …, true)`), and each
  user-owned table's policy admits only matching rows. The owner role is
  subject to it too (`FORCE`). Trusted server-side flows — login, the
  guest→account merge, the alert worker, the scripts — run with
  `app.bypass_rls = 'on'`, which is a connection setting rather than a separate
  role: the app is the only principal that holds the credentials, so a second
  role would add ceremony without a trust boundary.
- The public surface is `/health`, `/health/deep`, `/models`, and the session
  starts: `/auth/guest`, `/auth/login`, `/auth/signup`.

## CSRF

Two independent layers:

1. The cookie is `SameSite=Lax`, so browsers do not attach it to cross-site
   POST/PUT/PATCH/DELETE.
2. The API refuses any state-changing request whose `Origin` header is present
   and not in `CORS_ORIGINS`. Browsers set `Origin` on every cross-origin write
   and page script cannot alter it.

## Abuse limits

Fixed-window, per IP. Redis-backed so they hold across instances; when Redis
is unreachable an in-process window takes over rather than failing open.

| Endpoint | Limit |
|---|---|
| `POST /auth/guest` | 20 / hour, then Turnstile challenge |
| `POST /auth/login` | 10 / 5 min |
| `POST /auth/signup` | 5 / hour |
| `POST /predictions/*` | 60 / 5 min |
| `POST /backtests/*` | 20 / 5 min |

**Client IP.** The trusted source, in order: `X-Client-IP` from the frontend
proxy when its `X-Proxy-Secret` matches (Vercel overwrites `X-Forwarded-For`
with the real address before the proxy runs, so it cannot be forged); otherwise
the header named by `TRUSTED_CLIENT_IP_HEADER`, which the platform's own edge
stamps (`CF-Connecting-IP` on Render, where Cloudflare fronts every service);
otherwise the rightmost *public* `X-Forwarded-For` entry, skipping the
private hops the balancer appends after the client; otherwise the socket peer.
The leftmost entry is never used — it is whatever the client typed.
`/health/deep` returns `proxy` and `client` so this can be checked from outside.

## Data protection

- **In transit:** HTTPS at both edges with HSTS; `sslmode=require` to Postgres
  in production; TLS (`rediss://`) to Redis recommended, plaintext warns.
- **At rest:** emails encrypted at the application layer (AES-256-GCM, per-row
  nonce, HKDF-separated keys from `EMAIL_ENCRYPTION_KEY`); a keyed HMAC column
  carries the uniqueness constraint so "is this email taken?" needs no
  decryption and a dump does not allow confirming guesses. Losing the key makes
  existing addresses unreadable — back it up. Rotation = re-encrypt every row
  (the introducing migration is the template).
- The app stores no card data, government identifiers or financial accounts.
- Upstream provider errors are logged server-side and returned as a generic
  502; unhandled exceptions as a bare 500.

## Secret hygiene

- Only `.env.example` templates are tracked; `.gitignore` covers every `.env*`
  variant, private keys, keystores and service-account JSON.
- `scripts/check-secrets.sh` scans tracked files, or `--history` for every blob
  in every commit. CI runs the history scan on every push. Pre-commit:
  `ln -s ../../scripts/check-secrets.sh .git/hooks/pre-commit`.
- If a secret ever lands in a commit, rotate it *first*; rewriting history is
  the second step.

## Known limitations

- **Guest data is per browser.** Clearing cookies, or 30 days of absence, loses
  a guest's watchlist. That is the trade-off for having no sign-up; saving an
  account is the fix and is offered in the header.
- **Bot protection is off until Turnstile keys are configured.** Rate limits
  still apply.
- **No MFA, no password reset, no account lockout** (rate limiting only).
- **Interactive API docs are public** at `/docs`, intentionally.
- **The demo account's credentials are published** in the README; treat
  anything stored in it as public.
- **The in-process rate-limit fallback is per instance** and resets on restart.
