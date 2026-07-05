const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_ORIGIN = new URL(API_URL).origin;
const isDev = process.env.NODE_ENV !== "production";

// Content-Security-Policy: scripts/styles self-hosted; network calls limited to
// the app itself + the backend API. 'unsafe-inline'/'unsafe-eval' concessions
// are what Next.js requires (eval only in dev for react-refresh).
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  `connect-src 'self' ${API_ORIGIN}${isDev ? " ws:" : ""}`,
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
