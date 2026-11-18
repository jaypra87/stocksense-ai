import type { Metadata } from "next";

export const metadata: Metadata = { title: "Paper portfolio" };

export default function PortfolioLayout({ children }: { children: React.ReactNode }) {
  return children;
}
