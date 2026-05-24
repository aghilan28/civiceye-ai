# CivicEye Runtime Operations Guide

## Local stack startup

Run `docker compose config` first, then `docker compose up -d postgres redis migrations backend-api civiceye-web prometheus grafana`. Start GPU workers only with the `gpu-worker` profile after NVIDIA runtime validation succeeds.

## Distributed topology

The backend owns API routing, Redis stream publication, Postgres durability, worker registration, worker heartbeats, replay recovery, websocket fanout, and Prometheus export. Workers claim only queues they registered for and can be drained before restart.

## GPU worker deployment

Use `deploy/gpu-worker/.env.gpu-worker.example`, `deploy/gpu-worker/docker-compose.gpu-worker.yml`, or `deploy/helm/gpu-worker`. Validate CUDA with `deploy/gpu-worker/validate-worker-runtime.sh` before registering the worker.

## Queue architecture

Inference jobs are persisted in Postgres and mirrored to Redis streams. Consumer groups are created durably, Redis pending entries are reclaimed during startup recovery, and job execution is protected by claim IDs.

## Orchestration lifecycle

Jobs route by requested queue, model GPU requirements, and priority. Workers are selected by registered queue, model compatibility, online heartbeat, and saturation. Completion, failure, timeout, cancellation, replay, and recovery are inserted into `inference_job_events`.

## Replay and dead-letter flows

Jobs enter `DEAD_LETTER` after max attempts or unrecoverable timeout. Operators replay with `/api/v1/distributed/dead-letter/replay` after correcting the model/artifact/source issue. Replay emits `civiceye_dead_letter_replayed_total` and `civiceye_replay_recovery_total`.

## Observability setup

Prometheus scrapes `/metrics`. Grafana dashboards in `telemetry/grafana` use real `civiceye_*` metrics for queues, workers, GPUs, websockets, dependencies, replay, tenant activity, and inference lifecycle timing.

## Loki setup

Backend logs are structured JSON and include correlation, request, orchestration, worker, and inference trace IDs. Send container stdout to Loki using the cluster logging agent; the included Loki config is for local aggregation only.

## Kubernetes and Helm

Render manifests with `helm template civiceye deploy/helm/civiceye` and `helm template civiceye-gpu-worker deploy/helm/gpu-worker`. Secrets must provide database URL, Redis URL, JWT secret, worker shared secret, inference signing secret, and object-storage credentials.

## Object storage

Set `CIVICEYE_OBJECT_STORAGE_PROVIDER` to `local`, `s3`, `minio`, or `r2`. S3-compatible providers use SigV4 signed upload/download URLs and environment-driven bucket, endpoint, region, access key, secret key, public base URL, and artifact TTL settings.

## Model registry workflow

Register models with version, artifact URI, supported classes, latency profile, deployment target, capabilities, and optional checksum metadata. Promotion selects the active runtime version; rollback promotes the prior rollback version.

## Runtime diagnostics

Use `/runtime/diagnostics`, `/api/v1/storage/diagnostics`, `scripts/runtime_validation.py`, and `scripts/validate_manifests.py`. These checks validate local files, manifests, secrets shape, queues, DLQ inspectability, workers, websocket bus, storage, model artifact presence, and dependency reachability.

## Failure recovery

On startup, the backend expires stale workers, recovers timed-out jobs, reassigns orphaned jobs, republishes queued work, and reclaims Redis pending messages. Recovery emits `civiceye_recovery_actions_total` and JSON audit reports under `runtime/reports`.
