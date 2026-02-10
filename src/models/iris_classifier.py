"""Iris classifier implementation."""

import pickle
import time
from pathlib import Path
from typing import Any

import numpy as np

from src.models.interface import ModelInterface
from src.monitoring.metrics import INFERENCE_TIME, PREDICTION_COUNTER


class IrisClassifier(ModelInterface):
    """RandomForest classifier for Iris dataset."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self._load_model()

    def _load_model(self) -> None:
        """Load model from pickle file."""
        with open(self.model_path, "rb") as f:
            data = pickle.load(f)

        self.model = data["model"]
        self.feature_names = list(data["feature_names"])
        self.target_names = list(data["target_names"])
        self.version = data.get("version", "unknown")

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """Run prediction on input features."""
        # build feature array in correct order
        X = np.array([[features[name] for name in self.feature_names]])

        start = time.perf_counter()
        proba = self.model.predict_proba(X)[0]
        pred_idx = np.argmax(proba)
        elapsed = time.perf_counter() - start

        predicted_class = self.target_names[pred_idx]

        # record prometheus metrics
        INFERENCE_TIME.observe(elapsed)
        PREDICTION_COUNTER.labels(predicted_class=predicted_class).inc()

        return {
            "prediction": predicted_class,
            "confidence": float(proba[pred_idx]),
            "model_version": self.version,
            "inference_time_ms": round(elapsed * 1000, 3),
        }

    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata."""
        return {
            "name": "iris-classifier",
            "version": self.version,
            "framework": "sklearn",
            "features": self.feature_names,
            "classes": self.target_names,
        }
