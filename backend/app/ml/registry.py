"""On-disk model artifact storage. Knows nothing about the DB.

A "bundle" is everything needed to serve one horizon: the two fitted models,
the exact feature list they were trained on, and their evaluation metrics.
Bundles are saved with joblib under app/ml/artifacts/<version>/<horizon>.joblib.
The DB (model_artifacts table) records which bundle is active and, since the
hosting disk is ephemeral, also keeps a copy of the bytes so a fresh container
can put the file back without retraining (see `ensure_local`).
"""

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

logger = logging.getLogger(__name__)

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


class ModelNotReadyError(NoModelError):
    """A model is registered but its file is gone and nothing can restore it.

    This is the state right after a cold start on an ephemeral disk, while the
    bootstrap is still retraining: temporary, so callers should say "try again
    shortly" rather than "no model exists".
    """


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


def ensure_local(artifact: Any) -> Path:
    """Return a path on this machine for a registered artifact, restoring it
    from the stored bytes if the file was lost with the disk.

    `artifact` is a model_artifacts row (duck-typed: `.path`, `.model_version`,
    `.horizon`, `.blob`). The row's `path` is absolute and container-specific,
    so a restore goes to this process's own artifacts dir rather than there.
    """
    recorded = Path(artifact.path)
    if recorded.exists():
        return recorded
    local = bundle_path(artifact.model_version, artifact.horizon)
    if local.exists():
        return local
    if not artifact.blob:
        raise ModelNotReadyError(
            f"model {artifact.model_version}/{artifact.horizon} is not on disk "
            "and has no stored copy"
        )
    local.parent.mkdir(parents=True, exist_ok=True)
    # Write-then-rename so a concurrent reader never sees a half-written file.
    tmp = local.with_suffix(".joblib.part")
    tmp.write_bytes(artifact.blob)
    os.replace(tmp, local)
    logger.info("restored model %s/%s from database", artifact.model_version, artifact.horizon)
    return local
