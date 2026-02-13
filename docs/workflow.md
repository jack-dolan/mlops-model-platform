# Workflow

Here's what it looks like to go from "I trained a model" to "it's running in production":

**1. Train and track the experiment.** You train locally, but point MLflow at the tracking server so the run is recorded: parameters, metrics, and the model artifact (stored in S3). Each run automatically registers a new version in the MLflow model registry.

```bash
MLFLOW_TRACKING_URI=https://mlops-mlflow.dolanjack.com \
  python training/train_iris.py --n-estimators 150 --max-depth 5
```

You can view the run at [mlops-mlflow.dolanjack.com](https://mlops-mlflow.dolanjack.com). Compare accuracy across runs, see which hyperparameters worked, download previous model versions. Model artifacts are stored in S3 via the MLflow server's artifact proxy — no AWS credentials needed on the client.

**2. Promote the model.** When you're happy with a run, promote its version to "Production" in the MLflow model registry. The API loads the model from the registry at startup, so a pod restart picks up the new version — no image rebuild needed.

**3. CI runs automatically.** GitHub Actions lints the code, runs the test suite, and type-checks everything. If anything fails, the push is flagged before it goes further.

**4. Build and deploy.** On merge to main, CI builds a Docker image for both amd64 and arm64 and pushes it to GitHub Container Registry. The self-hosted runner on the Mac Mini pulls the arm64 image and deploys to staging automatically. Production requires manual approval.

**5. Monitor.** Grafana shows request latency, error rates, and prediction distribution in real time. If the model starts returning unusual predictions or latency spikes, you'll see it.

**6. Audit.** Every Monday, Prowler runs a security scan of the AWS setup, the script checks recent spending by service, and flags if billing alarms are missing. Results show up in the GitHub Actions logs.
