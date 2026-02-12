"""FastAPI application for model serving."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from src.api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
    ReadyResponse,
)
from src.models.iris_classifier import IrisClassifier
from src.monitoring.metrics import setup_metrics

logger = logging.getLogger(__name__)

# global model instance
model: IrisClassifier | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load model on startup — try MLflow registry first, fall back to pickle."""
    global model

    mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI")
    model_name = os.environ.get("MLFLOW_MODEL_NAME", "iris-classifier")
    model_stage = os.environ.get("MLFLOW_MODEL_STAGE", "Production")

    # try MLflow first
    if mlflow_uri:
        try:
            model = IrisClassifier.from_mlflow(mlflow_uri, model_name, model_stage)
            logger.info(
                "Loaded model from MLflow registry: %s version %s",
                model_name, model.version,
            )
        except Exception:
            logger.exception("Failed to load from MLflow, falling back to pickle")

    # fall back to pickle
    if model is None:
        model_path = Path(__file__).parent.parent.parent / "models" / "model.pkl"
        if model_path.exists():
            model = IrisClassifier(model_path)
            logger.info("Loaded model from %s", model_path)
        else:
            logger.warning("No model found — tried MLflow and %s", model_path)

    yield

    model = None


app = FastAPI(
    title="ML Model Service",
    description="Production ML model serving API",
    version="1.0.0",
    lifespan=lifespan,
)

setup_metrics(app)


@app.get("/health", response_model=HealthResponse)
async def health() -> dict[str, str]:
    """Liveness probe - is the service running?"""
    return {"status": "healthy"}


@app.get("/ready", response_model=ReadyResponse)
async def ready() -> dict[str, Any]:
    """Readiness probe - is the service ready to serve traffic?"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready", "model_loaded": True}


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest) -> dict[str, Any]:
    """Run inference on input features."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        result = model.predict(request.features)
        return result
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing feature: {e}") from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.get("/model/info", response_model=ModelInfoResponse)
async def model_info() -> dict[str, Any]:
    """Get model metadata."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return model.get_model_info()
