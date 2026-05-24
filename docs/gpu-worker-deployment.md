# CivicEye Remote GPU Worker Deployment

The local CivicEye stack runs web, backend API, Postgres/PostGIS, Redis, Prometheus, and Grafana without requiring CUDA. GPU inference workers run separately and register with the backend through signed worker registration.

## Required Runtime Values

- `CIVICEYE_BACKEND_URL`: reachable backend API URL
- `CIVICEYE_WORKER_SHARED_SECRET`: same high-entropy secret on backend and worker
- `CIVICEYE_QUEUE_NAMES`: comma-separated queues, for example `gpu.emergency,gpu.high,gpu.standard`
- `CIVICEYE_MODEL_DIR`: directory containing `best.pt` for compose deployments

## Docker Compose GPU Worker

```sh
cd deploy/gpu-worker
cp .env.gpu-worker.example .env.gpu-worker
docker compose --env-file .env.gpu-worker -f docker-compose.gpu-worker.yml up -d --build
```

Validate:

```sh
docker compose --env-file .env.gpu-worker -f docker-compose.gpu-worker.yml exec inference-worker-gpu sh /app/deploy/gpu-worker/validate-worker-runtime.sh
```

## Helm GPU Worker

Create a secret containing `database-url`, `redis-url`, and `worker-shared-secret`, then deploy:

```sh
helm upgrade --install civiceye-gpu-worker deploy/helm/gpu-worker \
  --set backend.url=https://api.civiceye.example.com \
  --set image.repository=ghcr.io/civiceye/civiceye-ai-backend \
  --set image.tag=latest
```

The chart schedules onto NVIDIA GPU nodes using `nvidia.com/gpu.present=true` and requests `nvidia.com/gpu`.

## Provider Notes

All providers use the same runtime contract: workers authenticate with HMAC-signed requests, call the backend over `CIVICEYE_BACKEND_URL`, and prove CUDA/model readiness with `validate-worker-runtime.sh` before being considered deployable.

RunPod:
- Startup: create a GPU pod with Docker support, attach persistent storage for `best.pt`, then run `deploy-runpod.sh`.
- Env template: start from `deploy/gpu-worker/.env.gpu-worker.example` and set `CIVICEYE_BACKEND_URL`, `CIVICEYE_WORKER_SHARED_SECRET`, `CIVICEYE_MODEL_DIR`, and queues.
- Validate: `docker compose --env-file .env.gpu-worker -f docker-compose.gpu-worker.yml exec inference-worker-gpu sh /app/deploy/gpu-worker/validate-worker-runtime.sh`.
- Troubleshoot: if validation fails, check RunPod GPU allocation, backend egress, mounted model path, and worker secret parity.

Vast.ai:
- Startup: select an NVIDIA Docker image host, clone the repo, configure `.env.gpu-worker`, then run `deploy-vast.sh`.
- Runtime verification: `nvidia-smi`, `docker compose ... ps`, and the worker validation script.
- Troubleshoot: prefer images with NVIDIA Container Toolkit already installed; failed CUDA checks usually mean the contract did not expose GPUs into Docker.

LambdaLabs:
- Startup: use an Ubuntu GPU instance, install Docker plus NVIDIA Container Toolkit, configure `.env.gpu-worker`, then run `deploy-cloud-vm.sh lambda`.
- Validate: run the worker validation script and confirm `/api/v1/distributed/topology` shows `ONLINE`.
- Troubleshoot: verify outbound HTTPS to the backend and model artifact permissions.

AWS GPU EC2:
- Startup: use an NVIDIA GPU AMI or install drivers/toolkit on a G5/G6/P-series instance, then run `deploy-cloud-vm.sh aws`.
- Health commands: `nvidia-smi`, `docker info | grep -i nvidia`, `docker compose --env-file .env.gpu-worker -f docker-compose.gpu-worker.yml logs --tail=120 inference-worker-gpu`.
- Troubleshoot: check security group egress to the backend and the model volume mount.

GCP GPU:
- Startup: create a GPU VM with NVIDIA drivers installed, attach persistent storage for model artifacts, then run `deploy-cloud-vm.sh gcp`.
- Validate: run `validate-worker-runtime.sh` and confirm Redis/Postgres are not required when `CIVICEYE_BACKEND_URL` is set.
- Troubleshoot: install the Container Toolkit after driver installation and reboot before running Docker.

Azure GPU:
- Startup: use an NC/ND-series VM with NVIDIA drivers and Docker runtime, then run `deploy-cloud-vm.sh azure`.
- Validate: `nvidia-smi`, the worker validation script, and backend topology.
- Troubleshoot: ensure the VM image exposes the GPU to containers and that managed identity/network rules allow backend egress.

Readiness is proven only when `/api/v1/distributed/topology` shows the worker `ONLINE`, with nonzero `gpu_count`, recent `last_heartbeat_at`, and queues matching the intended routing.

## Operational Checks

- Queue health: `/api/v1/distributed/topology` should show no stale workers and bounded `QUEUED`/`RETRY` depth.
- Worker drain: call `/api/v1/distributed/workers/{worker_id}/drain` through the signed worker flow before rolling restarts.
- Replay: use `/api/v1/distributed/dead-letter/replay` only after correcting the failing model/artifact/source condition.
- Metrics: scrape `/metrics` for `civiceye_queue_depth`, `civiceye_worker_heartbeat_age_seconds`, `civiceye_gpu_memory_mb`, `civiceye_inference_latency_ms`, and `civiceye_dead_letter_replayed_total`.
