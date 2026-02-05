# MLOps Model Serving Platform

Production-ready template for deploying ML models with full MLOps infrastructure, running on local hardware.

## Overview

A complete MLOps pipeline demonstrating how to take a trained ML model from notebook to production. The model itself is intentionally simple (Iris classifier) — the focus is on the infrastructure.

**Stack:** FastAPI, Docker, k3s (Kubernetes), GitHub Actions, MLflow, Prometheus/Grafana, Cloudflare Tunnel

## Quick Start

```bash
# setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# train the model
python training/train_iris.py

# run the API
uvicorn src.api.main:app --reload

# test
pytest
```

## Project Structure

```
src/
├── api/          # FastAPI application
├── models/       # Model interface + implementations
├── monitoring/   # Prometheus metrics
└── config.py     # Configuration
training/         # Model training scripts
tests/            # Test suite
docker/           # Dockerfile
kubernetes/       # K8s manifests (Kustomize)
```

## Status

Work in progress. See [API docs](http://localhost:8000/docs) when running locally.
