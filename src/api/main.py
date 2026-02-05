"""FastAPI application for model serving."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from src.api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
    ReadyResponse,
)
from src.models.iris_classifier import IrisClassifier


# global model instance
model: IrisClassifier | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup."""
    global model

    model_path = Path(__file__).parent.parent.parent / "models" / "model.pkl"

    if model_path.exists():
        model = IrisClassifier(model_path)
        print(f"Loaded model from {model_path}")
    else:
        print(f"Warning: model not found at {model_path}")

    yield  # app runs here

    # cleanup on shutdown (if needed)
    model = None


app = FastAPI(
    title="ML Model Service",
    description="Production ML model serving API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Liveness probe - is the service running?"""
    return {"status": "healthy"}


@app.get("/ready", response_model=ReadyResponse)
async def ready():
    """Readiness probe - is the service ready to serve traffic?"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready", "model_loaded": True}


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """Run inference on input features."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        result = model.predict(request.features)
        return result
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing feature: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/info", response_model=ModelInfoResponse)
async def model_info():
    """Get model metadata."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return model.get_model_info()
