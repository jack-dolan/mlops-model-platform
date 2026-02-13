# MLOps Model Serving Platform

A template for deploying ML models with real infrastructure (Docker, Kubernetes, CI/CD, monitoring) running on your own hardware.

[![CI](https://github.com/jack-dolan/mlops-model-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/jack-dolan/mlops-model-platform/actions/workflows/ci.yml)
[![Build](https://github.com/jack-dolan/mlops-model-platform/actions/workflows/build.yml/badge.svg)](https://github.com/jack-dolan/mlops-model-platform/actions/workflows/build.yml)

**Live API:** [mlops-api.dolanjack.com](https://mlops-api.dolanjack.com/docs)

---

## Overview

An MLOps pipeline for deploying ML models to production. The model is intentionally simple (Iris classifier) — the point is everything around it: the API, the container pipeline, the deployment automation, the monitoring, the experiment tracking. Swap in a different model and all of that infrastructure still works.

Built to close the gap between "I trained a model" and "it's running reliably in production."

**What makes this different:** Instead of running on managed cloud services, this runs on a Mac Mini in my home office. Same Kubernetes, same CI/CD, same monitoring — just with full control and about $0.50/month in cloud costs.

**What's included:**
- FastAPI model serving API with health checks and metrics
- Docker containerization with multi-stage builds
- Kubernetes (k3s) deployment with Kustomize overlays
- GitHub Actions CI/CD with self-hosted runner
- MLflow integration for experiment tracking (artifacts in S3)
- Prometheus + Grafana monitoring stack
- Automated AWS security scanning (Prowler), cost tracking, and billing alarms
- Secure external access via Cloudflare Tunnel

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 GitHub                                       │
│  ┌─────────────────────────┐           ┌─────────────────────────────────┐  │
│  │   GitHub Actions CI     │           │   GitHub Container Registry     │  │
│  │   (lint, test, build)   │──────────▶│   (ghcr.io)                     │  │
│  └─────────────────────────┘           └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                               │
                    ┌──────────────────────────┼───────────────────────────┐
                    ▼                          ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
│         AWS               │   │       Cloudflare          │   │   Mac Mini (Home Lab)     │
│                           │   │                           │   │                           │
│  ┌─────────────────────┐  │   │  ┌─────────────────────┐  │   │  ┌─────────────────────┐  │
│  │         S3          │  │   │  │      Tunnel         │  │   │  │    k3s Cluster      │  │
│  │  (MLflow artifacts) │  │   │  │  (secure ingress)   │◀─┼───│  │                     │  │
│  └─────────────────────┘  │   │  └─────────────────────┘  │   │  │  • Model Service    │  │
│                           │   │                           │   │  │  • MLflow Server    │  │
│  ┌─────────────────────┐  │   │  ┌─────────────────────┐  │   │  │  • Prometheus       │  │
│  │  Parameter Store    │  │   │  │        DNS          │  │   │  │  • Grafana          │  │
│  │     (secrets)       │  │   │  │  (dolanjack.com)    │  │   │  │  • GitHub Runner    │  │
│  └─────────────────────┘  │   │  └─────────────────────┘  │   │  └─────────────────────┘  │
│                           │   │                           │   │                           │
└───────────────────────────┘   └───────────────────────────┘   │  Hardware:                │
                                                                │  • Mac Mini M4            │
                                                                │  • 16GB RAM               │
                                                                │  • 256GB SSD              │
                                                                └───────────────────────────┘
```

---

## Quick Start

### Try the Live API

```bash
# Health check
curl https://mlops-api.dolanjack.com/health

# Get a prediction
curl -X POST https://mlops-api.dolanjack.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "sepal length (cm)": 5.1,
      "sepal width (cm)": 3.5,
      "petal length (cm)": 1.4,
      "petal width (cm)": 0.2
    }
  }'

# Response:
# {"prediction": "setosa", "confidence": 1.0, "model_version": "3", "inference_time_ms": 0.8}
```

### Local Development

```bash
# Clone the repo
git clone https://github.com/jack-dolan/mlops-model-platform.git
cd mlops-model-platform

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Train the example model
python training/train_iris.py

# Run the API locally
uvicorn src.api.main:app --reload

# Test it
curl http://localhost:8000/health
```

### Docker

```bash
# Build
docker build -t mlops-model:latest -f docker/Dockerfile .

# Run
docker run -p 8000:8000 mlops-model:latest
```

### Deploy to Your Own k3s Cluster

```bash
# Prerequisites: k3s installed, kubectl configured

# Deploy to staging
kubectl apply -k kubernetes/overlays/staging

# Verify
kubectl get pods -n staging
kubectl port-forward svc/model-service 8000:80 -n staging

# Deploy to production
kubectl apply -k kubernetes/overlays/production
```

---

## API Reference

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe |
| POST | `/predict` | Run inference |
| GET | `/model/info` | Model metadata |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | OpenAPI documentation |

### Prediction Request

```json
{
  "features": {
    "sepal length (cm)": 5.1,
    "sepal width (cm)": 3.5,
    "petal length (cm)": 1.4,
    "petal width (cm)": 0.2
  }
}
```

### Prediction Response

```json
{
  "prediction": "setosa",
  "confidence": 1.0,
  "model_version": "3",
  "inference_time_ms": 0.8
}
```

---

## Project Structure

```
mlops-model-platform/
├── src/
│   ├── api/              # FastAPI application
│   ├── models/           # Model interface and implementations
│   └── monitoring/       # Prometheus metrics
├── training/             # Model training scripts
├── tests/                # Test suite
├── docker/               # Dockerfile
├── kubernetes/           # K8s manifests (Kustomize)
│   ├── base/             # Base manifests
│   ├── overlays/         # Environment-specific configs
│   ├── mlflow/           # MLflow deployment
│   └── cloudflared/      # Tunnel configuration
├── monitoring/           # Grafana dashboards
├── scripts/              # Utility scripts
└── .github/workflows/    # CI/CD pipelines
```

---

## CI/CD Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   PR Open    │────▶│   CI Tests   │────▶│    Build     │────▶│   Deploy     │
│              │     │  (GH-hosted) │     │  (GH-hosted) │     │(self-hosted) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                           │                     │                     │
                           ▼                     ▼                     ▼
                      lint, test,          Push to GHCR        kubectl apply
                      type check                               to k3s cluster
```

- **CI:** Runs on every PR (lint, format, type check, test)
- **Build:** Runs on merge to main (multi-arch image pushed to GHCR)
- **Deploy:** Self-hosted runner deploys to staging automatically, production requires approval

---

## Workflow

Here's what it looks like to go from "I trained a model" to "it's running in production":

**1. Train and track the experiment.** You train locally, but point MLflow at the tracking server so the run is recorded: parameters, metrics, and the model artifact (stored in S3). Each run automatically registers a new version in the MLflow model registry.

```bash
MLFLOW_TRACKING_URI=https://mlops-mlflow.dolanjack.com \
  python training/train_iris.py --n-estimators 150 --max-depth 5
```

You can view the run at [mlops-mlflow.dolanjack.com](https://mlops-mlflow.dolanjack.com). Compare accuracy across runs, see which hyperparameters worked, download previous model versions. Model artifacts are stored in S3 via the MLflow server's artifact proxy — no AWS credentials needed on the client.

**2. Promote the model.** When you're happy with a run, promote its version to "Production" in the MLflow model registry. The API loads the model from the registry at startup, so a pod restart picks up the new version — no image rebuild needed.

**3. CI runs automatically.** GitHub Actions lints the code, runs the test suite, and type-checks everything. If anything fails, the push is flagged before it goes further.

**4. Build and deploy.** On merge to main, CI builds a multi-arch Docker image and pushes it to GitHub Container Registry. The self-hosted runner on the Mac Mini deploys to staging automatically. Production requires manual approval.

**5. Monitor.** Grafana shows request latency, error rates, and prediction distribution in real time. If the model starts returning unusual predictions or latency spikes, you'll see it.

**6. Audit.** Every Monday, Prowler runs a security scan of the AWS setup, the script checks recent spending by service, and flags if billing alarms are missing. Results show up in the GitHub Actions logs.

---

## Model Versioning & Rollback

The API pulls its model from the MLflow model registry on startup. Every training run auto-registers a new version, and the API serves whichever version is tagged "Production" — so you can swap models without rebuilding or redeploying the container.

**How it works:**
- `training/train_iris.py` logs the model to MLflow with `registered_model_name`, creating a new registry version each run
- On startup, the API reads `MLFLOW_TRACKING_URI` from the environment and calls `IrisClassifier.from_mlflow()` to load the Production-stage model
- If MLflow is unavailable (or not configured), it falls back to the pickle file baked into the Docker image

**Promoting a new model:**

```bash
# Train a new model (auto-registers as a new version)
MLFLOW_TRACKING_URI=https://mlops-mlflow.dolanjack.com \
  python training/train_iris.py --n-estimators 200 --max-depth 8

# Promote it to Production in MLflow
python -c "
from mlflow.tracking import MlflowClient
client = MlflowClient('https://mlops-mlflow.dolanjack.com')
client.transition_model_version_stage('iris-classifier', '<VERSION>', 'Production')
"

# Restart the pod to pick it up
kubectl rollout restart deploy/model-service -n production
```

**Rolling back:**

```bash
# Archive the bad version, restore the previous one
python -c "
from mlflow.tracking import MlflowClient
client = MlflowClient('https://mlops-mlflow.dolanjack.com')
client.transition_model_version_stage('iris-classifier', '<BAD_VERSION>', 'Archived')
client.transition_model_version_stage('iris-classifier', '<GOOD_VERSION>', 'Production')
"

# Restart the pod
kubectl rollout restart deploy/model-service -n production
```

Check which version is live at any time: `curl https://mlops-api.dolanjack.com/model/info`

---

## Swapping the Model

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

---

## Infrastructure Costs

| Component | Monthly Cost |
|-----------|-------------|
| AWS S3 (MLflow artifacts) | < $1 |
| AWS Parameter Store | $0 (free tier) |
| Cloudflare (Tunnel + DNS) | $0 |
| GitHub Container Registry | $0 |
| **Total** | **< $1/month** |

Plus one-time: Mac Mini M4 (about $600), domain (about $12/year)

---

## Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `http_request_duration_seconds` - Request latency histogram
- `http_requests_total` - Request counter by status code
- `model_inference_seconds` - Model inference time
- `predictions_total` - Predictions by class

Access the dashboards:
- **Grafana:** [mlops-grafana.dolanjack.com](https://mlops-grafana.dolanjack.com)
- **MLflow:** [mlops-mlflow.dolanjack.com](https://mlops-mlflow.dolanjack.com)

### Load Test Results

Tested with [hey](https://github.com/rakyll/hey) against the production `/predict` endpoint, going through Cloudflare Tunnel. 2 pod replicas on a Mac Mini M4.

| Concurrency | Throughput | p50 | p95 | p99 | Errors |
|-------------|-----------|-----|-----|-----|--------|
| 50 | 220 req/s | 189ms | 309ms | 812ms | 0% |
| 100 | 220 req/s | 307ms | 478ms | 3.1s | 0% |

Throughput plateaus around 220 req/s. Most of the latency is network (Cloudflare Tunnel round-trip), not inference — the model itself runs in under 1ms. p99 gets spiky at high concurrency but zero errors across all runs.

---

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Lint
ruff check src/

# Format
black src/

# Type check
mypy src/
```

---

## Why Self-Hosted?

Runs on my own hardware instead of EKS/GKE because:

1. **Cost:** Under a dollar a month vs $50-150/month for managed K8s
2. **Learning:** Managing k3s teaches more about Kubernetes internals than managed services
3. **Always-on:** No "oops I left the cluster running" cloud bills
4. **Full control:** I understand every component in the stack

Manifests are portable though — they'd work on EKS/GKE with minimal changes.

---

## Roadmap

- [x] FastAPI model serving
- [x] Docker containerization
- [x] k3s deployment
- [x] CI/CD pipeline with self-hosted runner
- [x] MLflow integration with S3
- [x] Prometheus + Grafana monitoring
- [x] Cloudflare Tunnel for external access
- [x] Model versioning and rollback (MLflow model registry promotion)
- [ ] Model drift detection
- [ ] A/B testing support

---

## License

MIT License - see [LICENSE](LICENSE) for details.
