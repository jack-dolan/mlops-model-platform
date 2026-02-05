"""Request/response schemas for the API."""

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Input features for prediction."""

    features: dict[str, float] = Field(
        ...,
        json_schema_extra={
            "example": {
                "sepal length (cm)": 5.1,
                "sepal width (cm)": 3.5,
                "petal length (cm)": 1.4,
                "petal width (cm)": 0.2,
            }
        },
    )


class PredictResponse(BaseModel):
    """Prediction result."""

    prediction: str
    confidence: float
    model_version: str
    inference_time_ms: float


class HealthResponse(BaseModel):
    """Health check response."""

    status: str


class ReadyResponse(BaseModel):
    """Readiness check response."""

    status: str
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    """Model metadata response."""

    name: str
    version: str
    framework: str
    features: list[str]
    classes: list[str]
