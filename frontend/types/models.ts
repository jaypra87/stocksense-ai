// Mirrors backend/app/schemas/model_info.py

export interface FeatureInfo {
  name: string;
  description: string;
}

export interface ModelVersionInfo {
  model_version: string;
  horizon: string;
  is_active: boolean;
  trained_at: string | null;
  metrics: {
    classifier?: { accuracy?: number; baseline_accuracy?: number };
    regressor?: { mae?: number; baseline_mae?: number };
    [k: string]: unknown;
  };
}

export interface ModelsInfo {
  data_sources: string[];
  features: FeatureInfo[];
  models: ModelVersionInfo[];
  methodology: string;
  limitations: string[];
  disclaimer: string;
}
