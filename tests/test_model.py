"""Tests for the Iris classifier."""

from unittest.mock import MagicMock, patch

import pytest

from src.models.iris_classifier import IrisClassifier


def test_model_loads(classifier: IrisClassifier):
    """Model should load without errors."""
    assert classifier.model is not None
    assert classifier.feature_names is not None
    assert classifier.target_names is not None


def test_model_has_correct_features(classifier: IrisClassifier):
    """Model should have the expected feature names."""
    expected = [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
    ]
    assert classifier.feature_names == expected


def test_model_has_correct_classes(classifier: IrisClassifier):
    """Model should have the expected class names."""
    expected = ["setosa", "versicolor", "virginica"]
    assert classifier.target_names == expected


def test_predict_returns_valid_response(
    classifier: IrisClassifier, sample_features: dict[str, float]
):
    """Prediction should return expected fields."""
    result = classifier.predict(sample_features)

    assert "prediction" in result
    assert "confidence" in result
    assert "model_version" in result
    assert "inference_time_ms" in result


def test_predict_setosa(classifier: IrisClassifier):
    """Small petals should predict setosa."""
    features = {
        "sepal length (cm)": 5.0,
        "sepal width (cm)": 3.5,
        "petal length (cm)": 1.3,
        "petal width (cm)": 0.2,
    }
    result = classifier.predict(features)
    assert result["prediction"] == "setosa"
    assert result["confidence"] > 0.9


def test_predict_confidence_range(
    classifier: IrisClassifier, sample_features: dict[str, float]
):
    """Confidence should be between 0 and 1."""
    result = classifier.predict(sample_features)
    assert 0 <= result["confidence"] <= 1


def test_predict_missing_feature(classifier: IrisClassifier):
    """Missing feature should raise KeyError."""
    incomplete = {
        "sepal length (cm)": 5.0,
        "sepal width (cm)": 3.5,
        # missing petal features
    }
    with pytest.raises(KeyError):
        classifier.predict(incomplete)


def test_get_model_info(classifier: IrisClassifier):
    """Model info should have expected fields."""
    info = classifier.get_model_info()

    assert info["name"] == "iris-classifier"
    assert info["framework"] == "sklearn"
    assert "version" in info
    assert "features" in info
    assert "classes" in info


def test_model_not_found():
    """Should raise error for missing model file."""
    with pytest.raises(FileNotFoundError):
        IrisClassifier("/nonexistent/path/model.pkl")


# --- MLflow loading tests ---


@patch("src.models.iris_classifier.MlflowClient")
@patch("src.models.iris_classifier.mlflow")
def test_from_mlflow(mock_mlflow, mock_client_cls):
    """Should load model from MLflow registry with correct metadata."""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    # fake registry version
    mock_version = MagicMock()
    mock_version.version = "3"
    mock_version.run_id = "abc123"
    mock_client.get_latest_versions.return_value = [mock_version]

    # fake run with tags
    mock_run = MagicMock()
    mock_run.data.tags = {
        "feature_names": "sepal length (cm),sepal width (cm),petal length (cm),petal width (cm)",
        "target_names": "setosa,versicolor,virginica",
    }
    mock_client.get_run.return_value = mock_run

    # fake sklearn model
    fake_model = MagicMock()
    mock_mlflow.sklearn.load_model.return_value = fake_model

    clf = IrisClassifier.from_mlflow(
        "http://mlflow:5000", "iris-classifier", "Production"
    )

    assert clf.version == "3"
    assert clf.model is fake_model
    assert clf.feature_names == [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
    ]
    assert clf.target_names == ["setosa", "versicolor", "virginica"]
    mock_mlflow.sklearn.load_model.assert_called_once_with(
        "models:/iris-classifier/Production"
    )


@patch("src.models.iris_classifier.MlflowClient")
@patch("src.models.iris_classifier.mlflow")
def test_from_mlflow_no_versions(mock_mlflow, mock_client_cls):
    """Should raise RuntimeError when no model at requested stage."""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.get_latest_versions.return_value = []

    with pytest.raises(RuntimeError, match="No model.*found at stage"):
        IrisClassifier.from_mlflow(
            "http://mlflow:5000", "iris-classifier", "Production"
        )
