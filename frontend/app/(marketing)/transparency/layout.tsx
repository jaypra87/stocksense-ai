import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Model transparency",
  description:
    "How StockSense AI produces its forecasts: data sources, features, model metrics, methodology, and known limitations.",
  alternates: { canonical: "/transparency" },
};

export default function TransparencyLayout({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">{children}</div>;
}
