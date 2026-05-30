from pydantic import BaseModel


class FeatureInfo(BaseModel):
    name: str
    description: str


class ModelVersionInfo(BaseModel):
    model_version: str
    horizon: str
    is_active: bool
    trained_at: str | None = None
    metrics: dict = {}


class ModelsOut(BaseModel):
    data_sources: list[str]
    features: list[FeatureInfo]
    models: list[ModelVersionInfo]
    methodology: str
    limitations: list[str]
    disclaimer: str
