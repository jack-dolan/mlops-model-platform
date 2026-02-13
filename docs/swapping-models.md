# Swapping the Model

The Iris classifier is a placeholder. To deploy a different model, you implement the model interface. It's two methods:

```python
class ModelInterface(ABC):
    @abstractmethod
    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """Takes feature dict, returns prediction dict."""
        pass

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Returns model metadata (name, version, features, etc.)."""
        pass
```

For example, here's what a wine quality classifier would look like:

```python
# src/models/wine_classifier.py
class WineClassifier(ModelInterface):
    def __init__(self, model_path):
        with open(model_path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
        self.version = data["version"]

    def predict(self, features):
        X = np.array([[features[name] for name in self.feature_names]])
        start = time.perf_counter()
        prediction = self.model.predict(X)[0]
        elapsed = time.perf_counter() - start

        INFERENCE_TIME.observe(elapsed)
        PREDICTION_COUNTER.labels(predicted_class=str(prediction)).inc()

        return {
            "prediction": int(prediction),
            "model_version": self.version,
            "inference_time_ms": round(elapsed * 1000, 3),
        }

    def get_model_info(self):
        return {
            "name": "wine-quality",
            "version": self.version,
            "framework": "sklearn",
            "features": self.feature_names,
        }
```

Then you'd need to:

1. **Write a training script** (`training/train_wine.py`). Load your dataset, train the model, save it as a pickle with the same structure (`model`, `feature_names`, `version`), and log the run to MLflow.
2. **Wire it up** in `src/api/main.py`. Swap `IrisClassifier` for `WineClassifier`.
3. **Update the tests.** The model-specific tests need to change (expected feature names, class names, sample predictions). The API tests (`test_health`, `test_ready`, `test_metrics_endpoint`) stay the same since they don't care which model is loaded.

The rest of the stack (Docker, Kubernetes, CI/CD, monitoring, Grafana dashboards) works without changes.
