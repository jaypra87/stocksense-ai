import type { Metadata } from "next";

export function generateMetadata({ params }: { params: { ticker: string } }): Metadata {
  const ticker = decodeURIComponent(params.ticker).toUpperCase();
  return { title: `${ticker} analysis` };
}

export default function StockLayout({ children }: { children: React.ReactNode }) {
  return children;
}
