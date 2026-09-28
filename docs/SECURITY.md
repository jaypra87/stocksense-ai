# Security posture

StockSense AI is an educational project with a public demo. This records what is
enforced, where the boundaries are, and — just as importantly — what is
deliberately *not* done, so the gaps are known rather than assumed away.

## Authentication

- Passwords are hashed with **bcrypt** (`app/core/security.py`). The plaintext is
  never stored or logged. The work factor is `BCRYPT_ROUNDS` (10–15, default 12);
  bcrypt records the cost inside each hash, so changing it never invalidates
  existing passwords.
- New passwords are capped at 72 bytes, because bcrypt silently ignores anything
  beyond that — an uncapped field would let a user believe a long passphrase was
  fully protecting them when only its first 72 bytes were.
- Login compares against a dummy hash when the email is unknown, so a wrong email
  and a wrong password take the same time. Without it, response latency leaks
  which accounts exist.
- Sessions are **JWTs (HS256, 60 min)**. `JWT_SECRET` must be ≥32 random chars in
  production; the app refuses to boot on the placeholder or a short secret.

## Authorization

- **Server-side, not just in the UI.** `/stocks/*` and `/predictions/*` declare
  `Depends(get_current_user)` at *router* level, so a newly added route inherits
  it instead of shipping open. The browser's `AuthGuard` is a convenience, never
  the control.
- **Ownership is taken from the token, never the request body.** Every
  watchlist/alert/backtest query is scoped by `user_id`, and update/delete
  re-check ownership before mutating, so guessing a record id yields a 404 rather
  than someone else's data.
- Request schemas set `extra="forbid"`, so smuggling a field you don't own (e.g.
  `user_id`) is a 422 rather than a silently ignored key.
- The public surface is deliberately small: `/health`, `/health/deep`, `/models`
  (the transparency page is public marketing content) and the `/auth/login` and
  `/auth/signup` flows, which cannot require a token you don't have yet.

`tests/test_access_control.py` asserts all of the above, including a test that
fails when a new route is added without classifying it as public or protected.

## Abuse limits

Fixed-window, per-IP, in Redis, preferring `X-Forwarded-For` (Render and Vercel
terminate TLS in front of the app):

| Endpoint | Limit |
|---|---|
| `POST /auth/login` | 10 / 5 min |
| `POST /auth/signup` | 5 / hour |
| `POST /predictions/*` | 60 / 5 min |
| `POST /backtests/*` | 20 / 5 min |

Predictions and backtests are capped because each one runs model inference and
writes a row. The limiter **fails open** if Redis is down: for this threat model,
being able to log in matters more than strict limiting.

## Data protection

- **In transit:** HTTPS is terminated by the platform; production responses carry
  HSTS, plus `X-Content-Type-Options`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`, a `Permissions-Policy` and `Cache-Control:
  no-store`. In production the Postgres URL gets `sslmode=require` appended when
  it is missing, and a plaintext `redis://` to a remote host logs a warning.
- **At rest:** handled by the managed providers (Neon, Upstash). The app stores
  no card data, no government identifiers and no financial accounts — the
  sensitive fields are an email address and a bcrypt hash.
- CORS lists explicit origins; production refuses to boot with `*`, which is
  incompatible with the credentialed requests the frontend makes.
- Upstream provider errors are logged server-side and returned as a generic 502,
  so library internals and URLs never reach a client. Unhandled exceptions return
  a bare 500 for the same reason.

## Secret hygiene

- No `.env` file has ever been committed; `git log` and a full-history blob scan
  are both clean. Only `.env.example` templates are tracked.
- `.gitignore` ignores every `.env*` variant (re-allowing `*.example`) plus
  private keys, keystores and service-account JSON.
- `scripts/check-secrets.sh` scans tracked files, or `--history` for every blob
  in every commit. Wire it in as a pre-commit hook:
  `ln -s ../../scripts/check-secrets.sh .git/hooks/pre-commit`

If a secret ever does land in a commit, rewriting history is the *second* step.
Rotate the credential first: anything that reached a remote must be treated as
public regardless of what the history looks like afterwards.

## Known limitations

These are accepted trade-offs for an educational project, not oversights.

- **The JWT lives in `localStorage`, not an httpOnly cookie.** That means an XSS
  bug could read the token. It is the standard trade-off for a
  token-authenticated SPA on a different origin from its API, where cookies need
  `SameSite=None; Secure` and bring CSRF back with them. Moving to cookies is the
  single biggest available hardening, and it is a real refactor: cookie issuance,
  CORS credentials, CSRF tokens, and logout/refresh semantics.
- **No Postgres row-level security.** Isolation is enforced in the service layer
  and covered by tests. Database-level RLS would add defence in depth against an
  application bug, but the app connects as one owner role, so it would also need
  per-request `SET LOCAL` of the user id on every path — including the Celery
  worker and bootstrap script.
- **No token revocation.** A stolen JWT is valid until it expires (60 min). A
  denylist or short-lived tokens with refresh would fix it.
- **No MFA, no password-reset flow, no account lockout** (rate limiting only).
- **Interactive API docs are public** at `/docs`, intentionally — it is a
  portfolio project and the schema is not a secret.
- **The demo account's credentials are published** in the README. It is a shared
  sandbox; treat anything stored in it as public.
