# Model Versioning & Rollback

> **Retired deployment.** This describes how the platform ran on self-hosted
> Kubernetes until August 2026. The cluster has been decommissioned, so the
> hostnames below are placeholders and nothing is reachable. Kept because the
> mechanism is the point, not the addresses.

The API pulls its model from the MLflow model registry on startup. Every training run auto-registers a new version, and the API serves whichever version is tagged "Production" — so you can swap models without rebuilding or redeploying the container.

**How it works:**
- `training/train_iris.py` logs the model to MLflow with `registered_model_name`, creating a new registry version each run
- On startup, the API reads `MLFLOW_TRACKING_URI` from the environment and calls `IrisClassifier.from_mlflow()` to load the Production-stage model
- If MLflow is unavailable (or not configured), it falls back to the pickle file baked into the Docker image

## Promoting a new model

```bash
# Train a new model (auto-registers as a new version)
MLFLOW_TRACKING_URI=https://mlflow.example.com \
  python training/train_iris.py --n-estimators 200 --max-depth 8

# Promote it to Production in MLflow
python -c "
from mlflow.tracking import MlflowClient
client = MlflowClient('https://mlflow.example.com')
client.transition_model_version_stage('iris-classifier', '<VERSION>', 'Production')
"

# Restart the pod to pick it up
kubectl rollout restart deploy/model-service -n production
```

## Rolling back

```bash
# Archive the bad version, restore the previous one
python -c "
from mlflow.tracking import MlflowClient
client = MlflowClient('https://mlflow.example.com')
client.transition_model_version_stage('iris-classifier', '<BAD_VERSION>', 'Archived')
client.transition_model_version_stage('iris-classifier', '<GOOD_VERSION>', 'Production')
"

# Restart the pod
kubectl rollout restart deploy/model-service -n production
```

Check which version is live at any time: `curl https://model-api.example.com/model/info`
