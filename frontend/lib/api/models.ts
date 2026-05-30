import { apiFetch } from "@/lib/api/client";
import type { ModelsInfo } from "@/types/models";

export function getModels(): Promise<ModelsInfo> {
  return apiFetch<ModelsInfo>("/models");
}
