export type AlertType = "price_above" | "price_below" | "pct_change_above" | "risk_above";

export const ALERT_TYPE_LABELS: Record<AlertType, string> = {
  price_above: "Price above",
  price_below: "Price below",
  pct_change_above: "Daily % move above",
  risk_above: "Risk score above",
};

export interface Alert {
  id: string;
  ticker: string;
  alert_type: AlertType;
  threshold: number;
  active: boolean;
  last_triggered_at: string | null;
  created_at: string | null;
}

export interface AlertEvent {
  id: string;
  alert_id: string;
  ticker: string;
  alert_type: string;
  triggered_at: string | null;
  payload: { value?: number; threshold?: number; message?: string };
}
