import { apiFetch } from "@/lib/api/client";
import type { Alert, AlertEvent, AlertType } from "@/types/alert";

export function getAlerts(): Promise<Alert[]> {
  return apiFetch<Alert[]>("/alerts");
}

export function createAlert(
  ticker: string,
  alertType: AlertType,
  threshold: number,
): Promise<Alert> {
  return apiFetch<Alert>("/alerts", {
    method: "POST",
    body: { ticker, alert_type: alertType, threshold },
  });
}

export function updateAlert(
  id: string,
  changes: { threshold?: number; active?: boolean },
): Promise<Alert> {
  return apiFetch<Alert>(`/alerts/${id}`, { method: "PATCH", body: changes });
}

export function deleteAlert(id: string): Promise<void> {
  return apiFetch<void>(`/alerts/${id}`, { method: "DELETE" });
}

export function getAlertEvents(): Promise<AlertEvent[]> {
  return apiFetch<AlertEvent[]>("/alerts/events");
}
