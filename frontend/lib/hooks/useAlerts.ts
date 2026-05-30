"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createAlert,
  deleteAlert,
  getAlertEvents,
  getAlerts,
  updateAlert,
} from "@/lib/api/alerts";
import type { AlertType } from "@/types/alert";

const ALERTS_KEY = ["alerts"];
const EVENTS_KEY = ["alert-events"];

export function useAlerts() {
  return useQuery({ queryKey: ALERTS_KEY, queryFn: getAlerts });
}

export function useAlertEvents() {
  return useQuery({ queryKey: EVENTS_KEY, queryFn: getAlertEvents });
}

export function useAlertMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ALERTS_KEY });

  const create = useMutation({
    mutationFn: (v: { ticker: string; alertType: AlertType; threshold: number }) =>
      createAlert(v.ticker, v.alertType, v.threshold),
    onSuccess: invalidate,
  });
  const update = useMutation({
    mutationFn: (v: { id: string; changes: { threshold?: number; active?: boolean } }) =>
      updateAlert(v.id, v.changes),
    onSuccess: invalidate,
  });
  const remove = useMutation({ mutationFn: deleteAlert, onSuccess: invalidate });

  return { create, update, remove };
}
