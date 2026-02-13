# MLOps Model Serving Platform

A template for deploying ML models with real infrastructure (Docker, Kubernetes, CI/CD, monitoring) running on your own hardware.

[![Pipeline](https://github.com/jack-dolan/mlops-model-platform/actions/workflows/pipeline.yml/badge.svg)](https://github.com/jack-dolan/mlops-model-platform/actions/workflows/pipeline.yml)

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
- MLflow experiment tracking + [model versioning/rollback](docs/model-versioning.md) via registry
- Prometheus + Grafana [monitoring](docs/monitoring.md) with load-tested performance numbers
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
                      type check                               to k3s cluster
```

- **CI:** Runs on every push and PR (lint, format, type check, test)
- **Build:** Runs on push to main. Builds for both `linux/amd64` and `linux/arm64` (dev machine is x86, Mac Mini is Apple Silicon) and pushes to GHCR.
- **Deploy:** Self-hosted runner deploys to staging automatically, production requires approval. Prunes unused container images from the node after each deploy.
- **Cleanup:** After each build, old untagged image versions are pruned from GHCR to keep storage in check.

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
│   └── cloudflared/      # Tunnel configuration
├── monitoring/           # Grafana dashboards
├── scripts/              # Utility scripts
├── docs/                 # Additional documentation
└── .github/workflows/    # CI/CD pipelines
```

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
