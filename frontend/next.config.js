const isDev = process.env.NODE_ENV !== "production";

// Cloudflare Turnstile (bot check) runs from this origin: its script, and an
// iframe for the (usually invisible) challenge.
const TURNSTILE = "https://challenges.cloudflare.com";

// Content-Security-Policy: scripts/styles self-hosted, plus Turnstile; network
// calls limited to this origin (the API is proxied under /api/v1, so the
// backend's address never appears here). 'unsafe-inline'/'unsafe-eval'
// concessions are what Next.js requires (eval only in dev for react-refresh).
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline' ${TURNSTILE}${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  `connect-src 'self' ${TURNSTILE}${isDev ? " ws:" : ""}`,
  `frame-src ${TURNSTILE}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  // HSTS: Vercel serves HTTPS only; browsers that see this never try http://.
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  images: {
    // Company logos (components/shared/TickerLogo). Served through the Next
    // image optimizer, so the CSP img-src stays same-origin.
    remotePatterns: [{ protocol: "https", hostname: "assets.parqet.com" }],
  },
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

module.exports = nextConfig;
