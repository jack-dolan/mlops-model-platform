"""Pytest fixtures."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.models.iris_classifier import IrisClassifier


@pytest.fixture
def model_path() -> Path:
    """Path to the trained model."""
    return Path(__file__).parent.parent / "models" / "model.pkl"


@pytest.fixture
def classifier(model_path: Path) -> IrisClassifier:
    """Loaded classifier instance."""
    return IrisClassifier(model_path)


@pytest.fixture
def client():
    """FastAPI test client with lifespan."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_features() -> dict[str, float]:
    """Sample input features (setosa)."""
    return {
        "sepal length (cm)": 5.1,
        "sepal width (cm)": 3.5,
        "petal length (cm)": 1.4,
        "petal width (cm)": 0.2,
    }
