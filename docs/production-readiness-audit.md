# CivicEye Production Readiness Audit

Date: 2026-05-18

## Existing Implementation State

- Frontend: Next.js App Router with command center, GIS, AI, analytics, field, reports, onboarding, admin, and PWA surfaces.
- Backend: FastAPI with image/video inference, live websocket inference, persisted municipal operations routes, enterprise intelligence routes, Prometheus metrics, Postgres access, and distributed worker entrypoints.
- AI: trained YOLOv8 pothole artifact at `ai/checkpoints/best.pt`, dataset/export tooling, evaluation tests, MLflow/W&B dependencies, ONNX/export tooling, and inference normalization tests.
- Data: Prisma schema models municipalities, districts, incidents, detections, media, field workers, repair tasks, model registry, inference jobs, edge devices, knowledge graph edges, predictions, emergency events, drift events, and analytics snapshots.
- Infrastructure: Dockerfiles, Docker Compose with PostGIS/Redis/API/web/worker/Prometheus/Grafana, Kubernetes baseline manifest, Prometheus scrape config, and GitHub Actions CI.

## Repairs Completed In This Pass

- Added backend runtime diagnostics at `/runtime/diagnostics`.
- Added reusable runtime validation scripts:
  - `scripts/runtime_validation.py`
  - `scripts/validate-runtime.ps1`
- Added package validation scripts:
  - `npm run validate:runtime`
  - `npm run validate:runtime:model`
- Corrected default YOLO weights path to `ai/checkpoints/best.pt` so local runtime uses the trained model before fallback weights.
- Reworked distributed inference worker so resolvable image/video jobs execute real YOLO inference and unresolved media jobs fail explicitly.
- Added frontend health endpoint at `/api/health`.
- Added Docker health checks for frontend and AI backend.
- Added Redis health check and health-gated service ordering in Docker Compose.
- Added `.dockerignore` to remove raw datasets, logs, build outputs, node modules, runtime media, and large archives from Docker build context.
- Extended CI with Python dependency installation, Prisma validation, AI tests, runtime validation, and Docker Compose config validation.
- Fixed AI training config path resolution so tests pass from the repository root.

## Stabilization Completed On 2026-05-19

- Completed a fresh runtime audit of executable repository paths before implementation.
- Connected frontend login to the real `/api/v1/auth/login` runtime path.
- Added frontend access/refresh token persistence and automatic access-token refresh through the shared API client.
- Switched operations and enterprise frontend API services from anonymous `fetch` calls to the token-aware shared API client.
- Propagated access tokens, municipality IDs, and channel subscriptions into operations websocket URLs.
- Added session hydration so browser refreshes restore authenticated runtime state from the token vault.
- Removed demo bypass from protected operational routes except `/demo`.
- Added backend refresh-token rotation checks and logout session invalidation.
- Enforced backend RBAC and tenant isolation on operations incident, analytics, enterprise intelligence, AI model, inference, emergency, tenant, billing, copilot, graph, disaster, and cost endpoints.
- Added `platform_admin` to runtime role handling while mapping it to the existing database `SYSTEM_ADMIN` enum for audit logs.
- Updated realtime event handling to cover backend emergency and tenant provisioning events.
- Completed frontend issue-to-department routing for all currently declared civic issue types.
- Completed frontend RBAC matrix entries for all declared user roles.

## Validated

- TypeScript contract check: passed.
- Next.js production build: passed.
- Python compile check for backend/runtime/scripts: passed.
- Prisma schema validation with `DATABASE_URL`: passed.
- AI unit test suite: 17 passed.
- Real YOLO model load: passed using `ai/checkpoints/best.pt`.
- Real image inference: passed on `ai/exports/yolo/pothole_v0.2.0/images/val/img-1.jpg` with 2 detections on CPU.
- Backend boot smoke test: passed on port 8099 with `/health` returning loaded model state.
- 2026-05-19 TypeScript contract check: passed after auth/realtime/RBAC stabilization.
- 2026-05-19 Python compile check for backend and scripts: passed after backend RBAC/auth stabilization.
- 2026-05-19 Prisma schema validation with local `DATABASE_URL`: passed.
- 2026-05-19 Runtime validation reached real infrastructure checks using Windows Python 3.12 and backend dependencies.

## Current Production Blockers

- Docker CLI is not available on the local PATH, so local Docker build/compose boot validation could not run here.
- kubectl is not available on the local PATH, so Kubernetes client validation could not run here.
- Local Postgres/PostGIS is not accepting connections at `localhost:5432`.
- Local Redis is not accepting connections at `localhost:6379`.
- The runtime validator correctly fails until real Postgres and Redis are reachable.
- CUDA is not available on this local machine; GPU deployment must be validated on a CUDA-capable VM or node.
- The shell default `python` points to MSYS Python without `pip`; use `py -3.12 scripts/runtime_validation.py` or install backend dependencies into the default interpreter.
- Terraform/cloud deployment is not validated from this workstation because provider credentials and deployment CLIs are not available.
- Stripe billing remains schema/runtime-metering level only; no production Stripe API keys or webhook endpoint validation were available in this environment.
- Kafka/Redpanda is declared as a runtime setting but no reachable broker was available for stream validation in this environment.
- Mobile native app and edge packaging are not present as runnable mobile/edge projects in the current repository state; PWA/offline and backend edge planning modules exist, but native builds were not validated.

## Runtime Gate

Before launch, `scripts/runtime_validation.py --load-model` must pass with:

- production `DATABASE_URL`
- production `REDIS_URL`
- high-entropy `CIVICEYE_JWT_SECRET`
- `CIVICEYE_MODEL_WEIGHTS` pointing to the promoted YOLO artifact
- Docker and kubectl available in the deployment runner
- reachable PostGIS and Redis instances

The platform should not be marked production-ready until that gate returns `status: ok`.
