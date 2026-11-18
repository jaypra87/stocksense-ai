import type { Metadata } from "next";

export const metadata: Metadata = { title: "Stock-man" };

export default function StockmanLayout({ children }: { children: React.ReactNode }) {
  return children;
}
