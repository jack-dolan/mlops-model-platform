"""Tests for the FastAPI endpoints."""

from fastapi.testclient import TestClient


def test_health(client: TestClient):
    """Health endpoint should return healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ready(client: TestClient):
    """Ready endpoint should return ready when model is loaded."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["model_loaded"] is True


def test_model_info(client: TestClient):
    """Model info endpoint should return metadata."""
    response = client.get("/model/info")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "iris-classifier"
    assert data["framework"] == "sklearn"
    assert len(data["features"]) == 4
    assert len(data["classes"]) == 3


def test_predict_success(client: TestClient, sample_features: dict[str, float]):
    """Predict endpoint should return valid prediction."""
    response = client.post("/predict", json={"features": sample_features})
    assert response.status_code == 200

    data = response.json()
    assert data["prediction"] in ["setosa", "versicolor", "virginica"]
    assert 0 <= data["confidence"] <= 1
    assert "model_version" in data
    assert "inference_time_ms" in data


def test_predict_setosa(client: TestClient):
    """Should predict setosa for small petals."""
    features = {
        "sepal length (cm)": 5.1,
        "sepal width (cm)": 3.5,
        "petal length (cm)": 1.4,
        "petal width (cm)": 0.2,
    }
    response = client.post("/predict", json={"features": features})
    assert response.status_code == 200
    assert response.json()["prediction"] == "setosa"


def test_predict_missing_feature(client: TestClient):
    """Should return 400 for missing features."""
    incomplete = {
        "sepal length (cm)": 5.0,
        # missing other features
    }
    response = client.post("/predict", json={"features": incomplete})
    assert response.status_code == 400


def test_predict_invalid_json(client: TestClient):
    """Should return 422 for invalid request body."""
    response = client.post("/predict", json={"wrong_field": "data"})
    assert response.status_code == 422


def test_metrics_endpoint(client: TestClient):
    """Prometheus metrics endpoint should return metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_request" in response.text


def test_openapi_docs(client: TestClient):
    """OpenAPI docs should be accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()
