# MLOps Model Serving Platform

A template for deploying ML models with real infrastructure (Docker, Kubernetes, CI/CD, monitoring) running on your own hardware.

[![CI](https://github.com/jack-dolan/mlops-model-platform/actions/workflows/pipeline.yml/badge.svg)](https://github.com/jack-dolan/mlops-model-platform/actions/workflows/pipeline.yml)

> **Deployment retired, August 2026.** This platform ran for six months on
> self-hosted Kubernetes. The hardware has been decommissioned, so there is no
> longer a live endpoint. **The code, the manifests and the CI pipeline are
> unchanged and still run** — CI lints, type-checks, trains the model and runs
> the test suite on every push. The deployment manifests below describe the
> cluster as it actually ran; hostnames in them are placeholders.

---

## Overview

An MLOps pipeline for deploying ML models to production. The model is intentionally simple (Iris classifier) — the point is everything around it: the API, the container pipeline, the deployment automation, the monitoring, the experiment tracking. Swap in a different model and all of that infrastructure still works.

Built to close the gap between "I trained a model" and "it's running reliably in production."

**What made this different:** instead of managed cloud services, it ran on a
single self-hosted machine — same Kubernetes, same CI/CD, same monitoring, at
about $0.50/month in cloud costs.

**What's included:**
- FastAPI model serving API with health checks and metrics
- Docker containerization with multi-stage builds
- Kubernetes (k3s) deployment with Kustomize overlays
- GitHub Actions CI (lint, type-check, train, test) on every push
- MLflow experiment tracking + [model versioning/rollback](docs/model-versioning.md) via registry
- Prometheus + Grafana [monitoring](docs/monitoring.md) with load-tested performance numbers
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
│         AWS               │   │       Cloudflare          │   │   Self-hosted node        │
│                           │   │                           │   │                           │
│  ┌─────────────────────┐  │   │  ┌─────────────────────┐  │   │  ┌─────────────────────┐  │
│  │         S3          │  │   │  │      Tunnel         │  │   │  │    k3s Cluster      │  │
│  │  (MLflow artifacts) │  │   │  │  (secure ingress)   │◀─┼───│  │                     │  │
│  └─────────────────────┘  │   │  └─────────────────────┘  │   │  │  • Model Service    │  │
│                           │   │                           │   │  │  • MLflow Server    │  │
│  ┌─────────────────────┐  │   │  ┌─────────────────────┐  │   │  │  • Prometheus       │  │
│  │  Parameter Store    │  │   │  │        DNS          │  │   │  │  • Grafana          │  │
│  │     (secrets)       │  │   │  │   (your domain)     │  │   │  │  • GitHub Runner    │  │
│  └─────────────────────┘  │   │  └─────────────────────┘  │   │  └─────────────────────┘  │
│                           │   │                           │   │                           │
└───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

---

## Quick Start

### Try the API (run it locally — see Local Development below)

```bash
# Health check
curl http://localhost:8000/health

# Get a prediction
curl -X POST http://localhost:8000/predict \
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
git clone https://github.com/jack-dolan/mlops-model-platform.git
cd mlops-model-platform

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

python training/train_iris.py        # train the model
uvicorn src.api.main:app --reload    # run the API
curl http://localhost:8000/health     # test it
```

### Docker

```bash
docker build -t mlops-model:latest -f docker/Dockerfile .
docker run -p 8000:8000 mlops-model:latest
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe |
| POST | `/predict` | Run inference |
| GET | `/model/info` | Model metadata |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | OpenAPI documentation |

### Prediction Request / Response

```json
// POST /predict
{"features": {"sepal length (cm)": 5.1, "sepal width (cm)": 3.5, "petal length (cm)": 1.4, "petal width (cm)": 0.2}}

// Response
{"prediction": "setosa", "confidence": 1.0, "model_version": "3", "inference_time_ms": 0.8}
```

---

## CI/CD Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Push/PR     │────▶│   CI Tests   │────▶│    Build     │────▶│   Deploy     │
│              │     │  (GH-hosted) │     │  (GH-hosted) │     │(self-hosted) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                           │                     │                     │
                           ▼                     ▼                     ▼
                      lint, test,          Push to GHCR        kubectl apply
                      type check           (retired)           (retired)
```

- **CI:** runs on every push and pull request — lint, format check, type check, train the model, run the test suite. **This is the only stage that still runs.**
- **Build, deploy and cleanup** published a multi-arch image to GHCR and applied the Kustomize manifests to the cluster via a self-hosted runner. All three were removed in August 2026 when the cluster was decommissioned; the runner they needed no longer exists.

See [docs/workflow.md](docs/workflow.md) for the full end-to-end walkthrough.

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
│   └── monitoring/       # Grafana ingress
├── monitoring/           # Grafana dashboards
├── scripts/              # Utility scripts
├── docs/                 # Additional documentation
└── .github/workflows/    # CI
```

---

## Infrastructure Costs

What it cost while it ran:

| Component | Monthly Cost |
|-----------|-------------|
| AWS S3 (MLflow artifacts) | < $1 |
| AWS Parameter Store | $0 (free tier) |
| Cloudflare (Tunnel + DNS) | $0 |
| GitHub Container Registry | $0 |
| **Total** | **< $1/month** |

Plus one-time hardware (a small Apple Silicon desktop) and a domain at about
$12/year. Every one of these resources has since been deleted, so the running
cost today is $0.

---

## Why Self-Hosted?

Runs on my own hardware instead of EKS/GKE because:

1. **Cost:** Under a dollar a month vs $50-150/month for managed K8s
2. **Learning:** Managing k3s teaches more about Kubernetes internals than managed services
3. **Always-on:** No "oops I left the cluster running" cloud bills
4. **Full control:** I understand every component in the stack

Manifests are portable though — they'd work on EKS/GKE with minimal changes.

---

## Documentation

- [End-to-end workflow](docs/workflow.md) — from training to production
- [Model versioning & rollback](docs/model-versioning.md) — promote and rollback models via MLflow
- [Swapping the model](docs/swapping-models.md) — how to deploy a different model
- [Monitoring & performance](docs/monitoring.md) — metrics, dashboards, load test results

---

## Development

```bash
pytest                              # run tests
pytest --cov=src --cov-report=html  # with coverage
ruff check src/                     # lint
black src/                          # format
mypy src/                           # type check
```

---

## Roadmap

- [x] FastAPI model serving
- [x] Docker containerization
- [x] k3s deployment
- [x] CI/CD pipeline with self-hosted runner *(deployment stages retired 2026-08)*
- [x] MLflow integration with S3
- [x] Prometheus + Grafana monitoring
- [x] Cloudflare Tunnel for external access
- [x] Model versioning and rollback (MLflow model registry promotion)
- [ ] Model drift detection
- [ ] A/B testing support

---

## License

MIT License - see [LICENSE](LICENSE) for details.
