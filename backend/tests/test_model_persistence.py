"""The hosting disk is ephemeral, so a trained bundle must survive in the DB
and come back without a retrain; while it cannot, the API must say so with a
503 rather than a 500. See app/ml/registry.ensure_local."""

from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import predictions as predictions_api
from app.ml import registry
from app.ml.registry import ModelNotReadyError, NoModelError
from app.services import prediction_service


@dataclass
class _Artifact:
    """Duck-typed model_artifacts row."""

    path: str
    model_version: str
    horizon: str
    blob: bytes | None


@pytest.fixture
def artifacts_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(registry, "ARTIFACTS_DIR", tmp_path)
    return tmp_path


def test_ensure_local_prefers_the_recorded_file(artifacts_dir: Path) -> None:
    recorded = artifacts_dir / "elsewhere" / "7d.joblib"
    recorded.parent.mkdir()
    recorded.write_bytes(b"on disk")
    art = _Artifact(str(recorded), "v1", "7d", blob=b"from db")

    assert registry.ensure_local(art) == recorded
    assert recorded.read_bytes() == b"on disk"


def test_ensure_local_restores_a_lost_file_from_the_db_copy(artifacts_dir: Path) -> None:
    # The recorded path is from a previous container and does not exist here.
    art = _Artifact("/gone/v1/7d.joblib", "v1", "7d", blob=b"bundle bytes")

    local = registry.ensure_local(art)

    assert local == artifacts_dir / "v1" / "7d.joblib"
    assert local.read_bytes() == b"bundle bytes"
    assert not list(artifacts_dir.glob("**/*.part")), "temp file must be renamed away"


def test_ensure_local_reports_not_ready_when_nothing_can_restore(artifacts_dir: Path) -> None:
    art = _Artifact("/gone/v1/7d.joblib", "v1", "7d", blob=None)

    with pytest.raises(ModelNotReadyError):
        registry.ensure_local(art)


def test_warming_up_is_a_503_with_a_retry_message(
    client: TestClient, as_user, monkeypatch: pytest.MonkeyPatch
) -> None:
    as_user()

    def not_ready(*_args, **_kwargs):
        raise ModelNotReadyError("file gone, no blob")

    monkeypatch.setattr(prediction_service, "predict", not_ready)
    monkeypatch.setattr(predictions_api, "get_provider", lambda: object())

    resp = client.post("/api/v1/predictions/AAPL?horizon=7d")

    assert resp.status_code == 503
    assert "warming up" in resp.json()["detail"]


def test_no_model_at_all_is_a_different_503(
    client: TestClient, as_user, monkeypatch: pytest.MonkeyPatch
) -> None:
    as_user()

    def nothing(*_args, **_kwargs):
        raise NoModelError("never trained")

    monkeypatch.setattr(prediction_service, "predict", nothing)
    monkeypatch.setattr(predictions_api, "get_provider", lambda: object())

    resp = client.post("/api/v1/predictions/AAPL?horizon=7d")

    assert resp.status_code == 503
    assert "No trained model" in resp.json()["detail"]
