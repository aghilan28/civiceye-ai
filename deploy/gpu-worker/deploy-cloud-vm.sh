#!/usr/bin/env sh
set -eu

provider="${1:?usage: deploy-cloud-vm.sh aws|gcp|azure|lambda|lambdalabs}"
case "$provider" in
  aws|gcp|azure|lambda|lambdalabs) ;;
  *) echo "Unsupported provider: $provider" >&2; exit 2 ;;
esac

: "${CIVICEYE_BACKEND_URL:?set CIVICEYE_BACKEND_URL}"
: "${CIVICEYE_WORKER_SHARED_SECRET:?set CIVICEYE_WORKER_SHARED_SECRET}"

command -v nvidia-smi >/dev/null 2>&1 || {
  echo "nvidia-smi is not available. Install NVIDIA driver and container toolkit before deploying." >&2
  exit 1
}
nvidia-smi

docker compose --env-file .env.gpu-worker -f docker-compose.gpu-worker.yml up -d --build
docker compose --env-file .env.gpu-worker -f docker-compose.gpu-worker.yml exec inference-worker-gpu sh /app/deploy/gpu-worker/validate-worker-runtime.sh
docker compose --env-file .env.gpu-worker -f docker-compose.gpu-worker.yml ps
