const DASH = "—";

export function fmtCurrency(value: number | null | undefined, currency = "USD"): string {
  if (value == null) return DASH;
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return `$${value.toFixed(2)}`;
  }
}

export function fmtPercent(value: number | null | undefined): string {
  if (value == null) return DASH;
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function fmtSignedCurrency(value: number | null | undefined, currency = "USD"): string {
  if (value == null) return DASH;
  const sign = value >= 0 ? "+" : "";
  return `${sign}${fmtCurrency(value, currency)}`;
}

// Compact notation for big numbers: 1_850_000_000 -> "1.85B"
export function fmtCompact(value: number | null | undefined): string {
  if (value == null) return DASH;
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

export function isUp(change: number | null | undefined): boolean {
  return (change ?? 0) >= 0;
}

// Plain fixed-decimal number (no sign, no currency). For indicator values.
export function fmtNumber(value: number | null | undefined, digits = 2): string {
  if (value == null) return DASH;
  return value.toFixed(digits);
}

// A percent already expressed as a percent number (e.g. 22.4 -> "22.40%").
export function fmtPctValue(value: number | null | undefined, digits = 2): string {
  if (value == null) return DASH;
  return `${value.toFixed(digits)}%`;
}
