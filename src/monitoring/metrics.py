"""Prometheus metrics for model serving."""

from fastapi import FastAPI
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

INFERENCE_TIME = Histogram(
    "model_inference_seconds",
    "Time spent in model inference",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

PREDICTION_COUNTER = Counter(
    "predictions_total",
    "Total predictions made",
    ["predicted_class"],
)


def setup_metrics(app: FastAPI) -> None:
    """Attach prometheus instrumentation to the FastAPI app."""
    Instrumentator().instrument(app).expose(app)
