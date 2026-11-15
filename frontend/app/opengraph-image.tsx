import { ImageResponse } from "next/og";

import { SITE_NAME, SITE_TAGLINE } from "@/lib/site";

// The link preview card for LinkedIn, Slack, X and friends. Rendered once at
// build time by Next from this component; no image file to keep in sync.
// Satori (the renderer) needs explicit flex on any element with several
// children, and a text node plus a literal counts as several.
export const alt = `${SITE_NAME}: ${SITE_TAGLINE}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "64px 72px",
          background: "linear-gradient(135deg, #0b1120 0%, #121a30 100%)",
          color: "#e6edf7",
          fontFamily: "Inter, Helvetica, Arial, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <svg width="64" height="64" viewBox="0 0 32 32">
            <rect width="32" height="32" rx="7" fill="#5b8cff" fillOpacity="0.18" />
            <path
              d="M6 22 L12 15 L16 18 L26 8"
              fill="none"
              stroke="#5b8cff"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M20 8 H26 V14"
              fill="none"
              stroke="#5b8cff"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <div style={{ display: "flex", fontSize: 40, fontWeight: 700, letterSpacing: -1 }}>
            StockSense <span style={{ color: "#5b8cff", marginLeft: 12 }}>AI</span>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div style={{ fontSize: 72, fontWeight: 700, lineHeight: 1.05, letterSpacing: -2 }}>
            {`${SITE_TAGLINE}.`}
          </div>
          <div style={{ fontSize: 30, color: "#9fb0c9", lineHeight: 1.35, maxWidth: 980 }}>
            Confidence scores, expected ranges, the factors behind each call, and a backtest you
            can run yourself.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: 24,
            color: "#7f8fa8",
          }}
        >
          <div style={{ display: "flex", gap: 36 }}>
            <span>Forecasts</span>
            <span>Risk scoring</span>
            <span>News sentiment</span>
            <span>Backtesting</span>
          </div>
          <span>Educational use only</span>
        </div>
      </div>
    ),
    size,
  );
}
