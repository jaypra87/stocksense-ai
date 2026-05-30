"""On-disk model artifact storage. Knows nothing about the DB.

A "bundle" is everything needed to serve one horizon: the two fitted models,
the exact feature list they were trained on, and their evaluation metrics.
Bundles are saved with joblib under app/ml/artifacts/<version>/<horizon>.joblib.
The DB (model_artifacts table) records which bundle is active.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


@dataclass
class ModelBundle:
    horizon: str
    classifier: Any  # RandomForestClassifier
    regressor: Any  # RandomForestRegressor
    feature_names: list[str]
    classes: list[str]
    metrics: dict
    # Training-set feature stats, used for per-prediction z-score attribution.
    # Optional/defaulted so older pickled bundles still load.
    feature_means: dict | None = None
    feature_stds: dict | None = None


class NoModelError(Exception):
    """No active model artifact is available for the requested horizon."""


def bundle_path(version: str, horizon: str) -> Path:
    return ARTIFACTS_DIR / version / f"{horizon}.joblib"


def save_bundle(bundle: ModelBundle, version: str) -> str:
    path = bundle_path(version, bundle.horizon)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    return str(path)


@lru_cache(maxsize=16)
def load_bundle(path: str) -> ModelBundle:
    """Load and cache a bundle by path (loading a forest off disk isn't free)."""
    return joblib.load(path)
