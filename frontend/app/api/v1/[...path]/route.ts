import type { NextRequest } from "next/server";

/**
 * Same-origin API proxy.
 *
 * The browser only ever talks to `/api/v1/...` on this site; this handler
 * forwards each call to the FastAPI backend. Three things fall out of that:
 *
 * 1. The session cookie is first-party. Set by the backend, it attaches to
 *    this origin, so it can be `HttpOnly` + `SameSite=Lax` with no cross-site
 *    cookie gymnastics and no CSRF token dance.
 * 2. The backend's address never reaches the browser (BACKEND_URL is a
 *    server-side variable, not NEXT_PUBLIC_).
 * 3. The backend learns the real client IP from a header only we can set:
 *    `X-Client-IP`, authenticated by `X-Proxy-Secret`. On Vercel,
 *    `x-forwarded-for` is overwritten with the connecting address before any
 *    code runs, so it is trustworthy here even though it is not on the
 *    backend's side of the hop.
 */

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const PROXY_SECRET = process.env.API_PROXY_SECRET;

// Headers that describe the hop, not the message; never forwarded either way.
const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "transfer-encoding",
  "te",
  "trailer",
  "upgrade",
  "proxy-authorization",
  "proxy-authenticate",
  "host",
  "content-length",
  "content-encoding", // fetch() already decoded the body
]);

async function proxy(req: NextRequest, { params }: { params: { path: string[] } }) {
  const target = new URL(`/api/v1/${params.path.join("/")}`, BACKEND_URL);
  target.search = req.nextUrl.search;

  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (HOP_BY_HOP.has(key)) return;
    // Never let a client pre-fill the headers the backend trusts from us.
    if (key === "x-client-ip" || key === "x-proxy-secret") return;
    headers.set(key, value);
  });

  const clientIp = req.headers.get("x-forwarded-for")?.split(",")[0].trim() ?? req.ip ?? "";
  if (clientIp) headers.set("x-client-ip", clientIp);
  if (PROXY_SECRET) headers.set("x-proxy-secret", PROXY_SECRET);

  const hasBody = req.method !== "GET" && req.method !== "HEAD";
  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body: hasBody ? await req.arrayBuffer() : undefined,
      redirect: "manual",
      cache: "no-store",
    });
  } catch {
    return Response.json(
      { detail: "The API is unreachable right now. Please try again shortly." },
      { status: 502 },
    );
  }

  const out = new Headers();
  upstream.headers.forEach((value, key) => {
    if (HOP_BY_HOP.has(key) || key === "set-cookie") return;
    out.set(key, value);
  });
  // Set-Cookie must be copied one header at a time; joining them would corrupt
  // the cookie attributes.
  for (const cookie of upstream.headers.getSetCookie()) out.append("set-cookie", cookie);

  return new Response(upstream.body, { status: upstream.status, headers: out });
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE };
