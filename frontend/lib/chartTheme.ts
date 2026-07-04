// Shared Recharts styling so every chart matches the design tokens.

export const chartTooltipStyle: React.CSSProperties = {
  background: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: 8,
  fontSize: 12,
  boxShadow: "0 4px 16px rgb(0 0 0 / 0.15)",
};

export const chartAxisTick = { fontSize: 11, fill: "hsl(var(--muted-foreground))" };

export const chartAxisStroke = "hsl(var(--border))";
