import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "StockSense AI — Interpretable stock analytics",
    template: "%s · StockSense AI",
  },
  description:
    "Live quotes, technical indicators, ML trend forecasts with confidence ranges, news sentiment, risk scoring, and honest backtesting. Educational only — not financial advice.",
  keywords: [
    "stock analytics",
    "ML forecasts",
    "technical indicators",
    "risk scoring",
    "backtesting",
  ],
  openGraph: {
    type: "website",
    siteName: "StockSense AI",
    title: "StockSense AI — Interpretable stock analytics",
    description:
      "Interpretable, uncertainty-aware market analytics: forecasts with confidence ranges, transparent risk scoring, and honest backtests.",
    url: SITE_URL,
  },
  twitter: {
    card: "summary",
    title: "StockSense AI — Interpretable stock analytics",
    description:
      "Interpretable, uncertainty-aware market analytics. Educational only — not financial advice.",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f7f9fc" },
    { media: "(prefers-color-scheme: dark)", color: "#090d17" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
