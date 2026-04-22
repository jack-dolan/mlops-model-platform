# Mac Mini Infrastructure Overview

Context file for running additional projects on the Mac Mini alongside the MLOps platform.

---

## Hardware

| Property | Value |
|----------|-------|
| OS | macOS 15.6 (arm64) |
| CPU | 10 cores (Apple Silicon) |
| RAM | 16 GB |
| Disk | 228 GB total — 17 GB used, 131 GB free |
| Uptime | Essentially always on (71+ days at last check) |
| SSH | `jack@192.168.68.70` |

---

## SSH Access

```bash
ssh jack@192.168.68.70
```

Commands that need Homebrew tools (brew, kubectl, limactl, etc.) require an explicit PATH:

```bash
ssh jack@192.168.68.70 'export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH; <your command>'
```

---

## What's Installed (Homebrew)

| Package | Purpose |
|---------|---------|
| `lima` | VM manager — runs the k3s cluster |
| `kubernetes-cli` | kubectl |
| `helm` | Helm chart deployments |
| `docker` | Docker CLI (used with colima or remotely) |
| `colima` | Container runtime (installed but not currently running) |
| `cloudflared` | Cloudflare Tunnel CLI (tunnel runs inside k3s, not on host) |
| `awscli` | AWS CLI for S3/SSM access |
| `gh` | GitHub CLI |
| `tmux` | Terminal multiplexer — keeps the GH Actions runner alive |
| `python@3.13` | Python (note: mlops project uses python3.12 via venv) |
| `openssl@3`, `readline`, `sqlite`, `xz` | Common dependencies |

### Brew Services

Neither `cloudflared` nor `colima` run as host-level brew services. The Cloudflare tunnel runs as a pod inside k3s.

---

## Keeping Things Up to Date

The Mac Mini is headless — avoid triggering macOS system updates (they can break things and require a reboot you can't easily manage remotely).

```bash
# Update Homebrew packages
brew update && brew upgrade

# Check Lima VM health
limactl list

# k3s itself is managed by Lima — to update, you'd update the Lima template
# In practice: if it ain't broke, don't touch it
```

For security patches on macOS, either VNC in and do it manually, or accept the risk and keep critical services behind the tunnel only.

---

## Kubernetes Cluster (k3s via Lima)

k3s runs inside a Lima VM on the Mac Mini.

| Property | Value |
|----------|-------|
| VM name | `k3s` |
| VM CPUs | 8 (of 10 physical) |
| VM RAM | 8 GiB |
| VM Disk | 100 GiB |
| Status | Always running |

### kubectl Access (from Mac Mini)

```bash
export KUBECONFIG=$HOME/.lima/k3s/copied-from-guest/kubeconfig.yaml
kubectl get pods -A
```

### kubectl Access (from your desktop, if tunneled)

You'd need to copy the kubeconfig and patch the server address, or use SSH forwarding. Easiest is just to SSH to the Mac Mini and run kubectl there.

---

## Current Resource Usage

Snapshot from April 2026 — light load, plenty of headroom.

**Host (macOS):**
- CPU: ~5-15% used, ~85% idle
- RAM: ~15 GB in use by macOS (heavily compressed); Lima VM accounts for most of it
- Disk: 131 GB free

**k3s node (inside Lima VM — 8 CPU / 8 GiB):**
- CPU: ~222m used (~2% of 8000m capacity)
- RAM: ~4.3 GiB used (~53% of 8 GiB)

### Pod-level Memory Breakdown

| Namespace | Pod | Memory |
|-----------|-----|--------|
| kube-system | coredns | 76 Mi |
| kube-system | traefik | 121 Mi |
| kube-system | metrics-server | 76 Mi |
| kube-system | local-path-provisioner | 45 Mi |
| monitoring | prometheus | 623 Mi |
| monitoring | grafana | 478 Mi |
| monitoring | alertmanager | 58 Mi |
| monitoring | kube-prometheus-operator | 72 Mi |
| monitoring | kube-state-metrics | 67 Mi |
| monitoring | node-exporter | 24 Mi |
| production | model-service (×2) | 368 Mi |
| production | cloudflared | 36 Mi |
| staging | mlflow | 725 Mi |
| staging | model-service | 203 Mi |
| **Total** | | **~3.0 GiB** |

**Available headroom in k3s: ~3.7 GiB RAM, ~7.8 CPU cores.**

A new project running a few pods (say, a small API + a sidecar) would comfortably fit as long as it stays under ~2-3 GiB RAM total.

---

## What's Running and What It Does

### kube-system namespace
Core k3s infrastructure — don't touch.
- **coredns**: DNS resolution inside the cluster
- **traefik**: Ingress controller; handles all HTTP/HTTPS routing on ports 80/443
- **local-path-provisioner**: Handles PersistentVolumeClaims using local disk
- **metrics-server**: Enables `kubectl top`

### monitoring namespace
Full Prometheus + Grafana stack (kube-prometheus-stack).
- **prometheus**: Scrapes metrics from all pods with the right annotations/ServiceMonitors
- **grafana**: Dashboards at mlops-grafana.dolanjack.com
- **alertmanager**: Receives Prometheus alerts (not yet wired to Slack/PagerDuty)
- **kube-state-metrics**, **node-exporter**: Feed data to Prometheus

### production namespace
- **model-service** (2 replicas): FastAPI Iris classifier, served at mlops-api.dolanjack.com
- **cloudflared**: The Cloudflare Tunnel that exposes production services to the internet

### staging namespace
- **model-service** (1 replica): Staging version at mlops-api-staging.dolanjack.com
- **mlflow**: Experiment tracking server at mlops-mlflow.dolanjack.com

---

## Networking and External Access

External access goes through Cloudflare Tunnel (not open ports). The cloudflared pod in the `production` namespace connects outbound to Cloudflare and proxies traffic in. No inbound firewall rules needed.

**Current public routes:**

| URL | Destination |
|-----|-------------|
| mlops-api.dolanjack.com | production/model-service |
| mlops-api-staging.dolanjack.com | staging/model-service |
| mlops-mlflow.dolanjack.com | staging/mlflow |
| mlops-grafana.dolanjack.com | monitoring/grafana |

### Adding a New Public Endpoint

1. Add a new `hostname` entry to the cloudflared ConfigMap (in the `production` namespace) and restart the cloudflared pod.
2. Add a DNS CNAME on Cloudflare pointing `your-subdomain.dolanjack.com` → your tunnel ID.
3. Create an IngressRoute (or Ingress) in k3s so Traefik routes internal cluster traffic to the right service.

If the new project doesn't need public access, skip 1 and 2 — it's just internal cluster traffic.

### Traefik

Traefik is already running as the ingress controller. New services just need an `IngressRoute` or standard `Ingress` resource pointing to them. Traefik listens on the Lima VM IP (`192.168.5.15`) on ports 80 and 443.

---

## What Would and Wouldn't Conflict

### Safe — no conflict
- Deploying to a **new namespace** in k3s — fully isolated from existing workloads
- Using the **same Traefik ingress** with different hostnames/paths
- Adding new Prometheus `ServiceMonitor` resources — Prometheus will just scrape the new targets
- Running new containers from GHCR or Docker Hub
- Adding new cloudflared hostname routes (up to Cloudflare plan limits)

### Requires coordination
- **RAM**: The Lima VM has ~3.7 GiB headroom. MLflow alone uses 725 Mi and Prometheus uses 623 Mi. A memory-heavy workload (another ML model, a database) needs to be sized carefully. If you hit the 8 GiB limit, pods will OOM-kill.
- **Disk (PVCs)**: local-path provisioner writes to the Lima VM's 100 GiB disk. 17 GB already used on the host, plenty of room, but large model artifacts or databases could eat it fast.
- **GitHub Actions runner**: The tmux session `mlops-model-platform-actions-runner` is for the mlops repo specifically. A new project's runner would need its own tmux session and registration.
- **Cloudflare Tunnel**: The existing tunnel is configured for the mlops project's domains. Adding new routes to it is fine, but it means the mlops cloudflared pod is a single point of failure for all external access. If you want true isolation, run a separate tunnel pod in a new namespace.

### Would break things
- Deleting or modifying resources in `kube-system` or `monitoring`
- Changing the Lima VM's CPU/memory allocation while it's running (requires VM restart = brief k3s downtime)
- Touching MX records on dolanjack.com (Google Workspace email)
- Stopping the tmux session with the Actions runner without registering a new one

---

## Persistent State to Be Aware Of

- **MLflow artifacts**: stored in S3 (not on the Mac Mini disk)
- **Model artifacts**: stored in S3 / MLflow registry
- **Grafana dashboards**: stored in a PVC on the Mac Mini disk
- **Prometheus data**: stored in a PVC on the Mac Mini disk (retention: default 24h or whatever's configured)
- **k3s etcd**: cluster state lives inside the Lima VM

None of these back up automatically. A Lima VM corruption would lose Grafana dashboards and recent Prometheus data. S3 holds the important stuff.

---

## macOS Maintenance Notes

- No automatic updates — SSH in and run `brew update && brew upgrade` periodically
- If the Mac Mini reboots (power outage, etc.): Lima VM does **not** auto-start. You'd need to `limactl start k3s` after logging in, then confirm pods come back up.
- To auto-start Lima on login: `limactl start --keep-alive k3s` or add a launchd plist (not currently configured)
- The GitHub Actions runner in tmux will also die on reboot — it needs to be restarted manually or wired to launchd
