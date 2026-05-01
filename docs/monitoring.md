# Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `http_request_duration_seconds` - Request latency histogram
- `http_requests_total` - Request counter by status code
- `model_inference_seconds` - Model inference time
- `predictions_total` - Predictions by class

Access the dashboards:
- **Grafana:** [mlops-grafana.dolanjack.com](https://mlops-grafana.dolanjack.com)
- **MLflow:** [mlops-mlflow.dolanjack.com](https://mlops-mlflow.dolanjack.com)

## Alerting Rules

Prometheus alerting rules are defined in `kubernetes/base/prometheusrule.yaml` and deployed to both staging and production via Kustomize:

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighErrorRate | >5% of requests returning 5xx for 5 min | critical |
| HighP95Latency | p95 request latency >500ms for 5 min | warning |
| HighInferenceTime | p95 inference time >100ms for 5 min | warning |
| ServiceDown | Prometheus can't scrape service for 5 min | critical |

Thresholds are based on load test baselines — normal p95 latency is ~300ms (mostly network), normal inference time is <1ms.

## Load Test Results

Tested with [hey](https://github.com/rakyll/hey) against the production `/predict` endpoint, going through Cloudflare Tunnel. 2 pod replicas on a Mac Mini M4.

| Concurrency | Throughput | p50 | p95 | p99 | Errors |
|-------------|-----------|-----|-----|-----|--------|
| 50 | 220 req/s | 189ms | 309ms | 812ms | 0% |
| 100 | 220 req/s | 307ms | 478ms | 3.1s | 0% |

Throughput plateaus around 220 req/s. Most of the latency is network (Cloudflare Tunnel round-trip), not inference — the model itself runs in under 1ms. p99 gets spiky at high concurrency but zero errors across all runs.
