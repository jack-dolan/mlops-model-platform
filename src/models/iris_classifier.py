"""Iris classifier implementation."""

import logging
import pickle
import time
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn
import numpy as np
from mlflow.tracking import MlflowClient

from src.models.interface import ModelInterface
from src.monitoring.metrics import INFERENCE_TIME, PREDICTION_COUNTER

logger = logging.getLogger(__name__)


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

    @classmethod
    def from_mlflow(
        cls, tracking_uri: str, model_name: str, stage: str
    ) -> "IrisClassifier":
        """Load model from MLflow model registry."""
        mlflow.set_tracking_uri(tracking_uri)
        client = MlflowClient(tracking_uri)

        # find the latest version at the requested stage
        versions = client.get_latest_versions(model_name, stages=[stage])
        if not versions:
            raise RuntimeError(
                f"No model '{model_name}' found at stage '{stage}'"
            )

        mv = versions[0]
        logger.info(
            "Loading %s version %s (stage=%s, run=%s)",
            model_name, mv.version, stage, mv.run_id,
        )

        # load the sklearn model
        model_uri = f"models:/{model_name}/{stage}"
        sklearn_model = mlflow.sklearn.load_model(model_uri)

        # read feature/target names from run tags
        run = client.get_run(mv.run_id)
        tags = run.data.tags

        feature_str = tags.get("feature_names")
        target_str = tags.get("target_names")
        if not feature_str or not target_str:
            raise RuntimeError(
                f"Run {mv.run_id} missing feature_names/target_names tags"
            )

        # build instance without calling __init__
        instance = cls.__new__(cls)
        instance.model = sklearn_model
        instance.feature_names = feature_str.split(",")
        instance.target_names = target_str.split(",")
        instance.version = mv.version
        return instance

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
