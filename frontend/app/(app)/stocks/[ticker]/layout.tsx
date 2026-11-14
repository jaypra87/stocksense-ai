import type { Metadata } from "next";

export async function generateMetadata({ params }: { params: Promise<{ ticker: string }> }): Promise<Metadata> {
  const { ticker: raw } = await params;
  const ticker = decodeURIComponent(raw).toUpperCase();
  return { title: `${ticker} analysis` };
}

export default function StockLayout({ children }: { children: React.ReactNode }) {
  return children;
}
