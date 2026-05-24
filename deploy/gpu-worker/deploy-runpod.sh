#!/usr/bin/env sh
set -eu

: "${CIVICEYE_BACKEND_URL:?set CIVICEYE_BACKEND_URL}"
: "${CIVICEYE_WORKER_SHARED_SECRET:?set CIVICEYE_WORKER_SHARED_SECRET}"

docker compose --env-file .env.gpu-worker -f docker-compose.gpu-worker.yml up -d --build
docker compose --env-file .env.gpu-worker -f docker-compose.gpu-worker.yml exec inference-worker-gpu sh /app/deploy/gpu-worker/validate-worker-runtime.sh
