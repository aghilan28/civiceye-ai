# FINAL RUNTIME AUDIT

Generated: 2026-05-22T11:52:49.960227+00:00
Overall status: failed

## Results
[
  {
    "name": "critical_files",
    "status": "ok",
    "detail": "All critical runtime files exist.",
    "remediation": null
  },
  {
    "name": "typescript_typecheck",
    "status": "ok",
    "detail": "> civiceye@0.1.0 typecheck\n> tsc --noEmit",
    "remediation": null
  },
  {
    "name": "python_compile",
    "status": "ok",
    "detail": "Listing 'backend'...\nListing 'backend\\\\ai_platform'...\nListing 'backend\\\\api'...\nListing 'backend\\\\copilots'...\nListing 'backend\\\\database'...\nListing 'backend\\\\distributed'...\nListing 'backend\\\\edge'...\nListing 'backend\\\\gis'...\nListing 'backend\\\\gpu'...\nListing 'backend\\\\incidents'...\nListing 'backend\\\\inference'...\nListing 'backend\\\\mlops'...\nListing 'backend\\\\models'...\nListing 'backend\\\\operations'...\nListing 'backend\\\\prediction'...\nListing 'backend\\\\queues'...\nListing 'backend\\\\routing'...\nListing 'backend\\\\runtime'...\nListing 'backend\\\\security'...\nListing 'backend\\\\services'...\nListing 'backend\\\\storage'...\nListing 'backend\\\\telemetry'...\nListing 'backend\\\\tenants'...\nListing 'backend\\\\utils'...\nListing 'backend\\\\websocket'...\nListing 'scripts'...",
    "remediation": null
  },
  {
    "name": "prisma_schema",
    "status": "ok",
    "detail": "Prisma schema loaded from prisma\\schema.prisma\nThe schema at prisma\\schema.prisma is valid \u00f0\u0178\u0161\u20ac",
    "remediation": null
  },
  {
    "name": "docker_engine",
    "status": "failed",
    "detail": "Client:\n Version:           29.4.3\n API version:       1.54\n Go version:        go1.26.2\n Git commit:        055a478\n Built:             Wed May  6 17:10:36 2026\n OS/Arch:           windows/amd64\n Context:           desktop-linux\n\nrequest returned 500 Internal Server Error for API route and version http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.54/version, check if the server supports the requested API version",
    "remediation": null
  },
  {
    "name": "docker_compose_config",
    "status": "ok",
    "detail": "ok",
    "remediation": null
  },
  {
    "name": "kubernetes_manifest_client_validation",
    "status": "failed",
    "detail": "Command timed out after 45s: kubectl apply --dry-run=client --validate=false -f deploy/kubernetes/civiceye-enterprise.yaml",
    "remediation": "Inspect the command output and service health."
  },
  {
    "name": "helm_gpu_worker_template",
    "status": "ok",
    "detail": "---\n# Source: civiceye-gpu-worker/templates/pvc.yaml\napiVersion: v1\nkind: PersistentVolumeClaim\nmetadata:\n  name: civiceye-gpu-worker-runtime\nspec:\n  accessModes:\n    - ReadWriteOnce\n  resources:\n    requests:\n      storage: 50Gi\n\n---\n# Source: civiceye-gpu-worker/templates/deployment.yaml\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: civiceye-gpu-worker\n  labels:\n    app: civiceye-gpu-worker\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: civiceye-gpu-worker\n  template:\n    metadata:\n      labels:\n        app: civiceye-gpu-worker\n      annotations:\n        prometheus.io/scrape: \"false\"\n    spec:\n      nodeSelector:\n        nvidia.com/gpu.present: \"true\"\n      tolerations:\n        - effect: NoSchedule\n          key: nvidia.com/gpu\n          operator: Exists\n      containers:\n        - name: worker\n          image: \"ghcr.io/civiceye/civiceye-ai-backend:latest\"\n          imagePullPolicy: IfNotPresent\n          command: [\"python3\", \"-m\", \"backend.distributed.worker\"]\n          resources:\n            limits:\n              nvidia.com/gpu: 1\n          env:\n            - name: CIVICEYE_BACKEND_URL\n              value: \"https://api.civiceye.example.com\"\n            - name: CIVICEYE_WORKER_ID\n              valueFrom:\n                fieldRef:\n                  fieldPath: metadata.name\n            - name: CIVICEYE_QUEUE_NAMES\n              value: \"gpu.emergency,gpu.high,gpu.standard\"\n            - name: CIVICEYE_WORKER_CONCURRENCY\n              value: \"1\"\n            - name: CIVICEYE_MODEL_WEIGHTS\n              value: \"/models/best.pt\"\n            - name: CIVICEYE_STORAGE_DIR\n              value: \"/app/runtime/ai\"\n            - name: DATABASE_URL\n              valueFrom:\n                secretKeyRef:\n                  name: civiceye-gpu-worker-secrets\n                  key: database-url\n            - name: REDIS_URL\n              valueFrom:\n                secretKeyRef:\n                  name: civiceye-gpu-worker-secrets\n                  key: redis-url\n            - name: CIVICEYE_WORKER_SHARED_SECRET\n              valueFrom:\n                secretKeyRef:\n                  name: civiceye-gpu-worker-secrets\n                  key: worker-shared-secret\n          volumeMounts:\n            - name: runtime\n              mountPath: /app/runtime/ai\n            - name: model-artifacts\n              mountPath: /models\n              readOnly: true\n          readinessProbe:\n            exec:\n              command: [\"python3\", \"-c\", \"from backend.gpu.device import get_device_info; raise SystemExit(0 if get_device_info().cuda_available else 1)\"]\n            initialDelaySeconds: 30\n            periodSeconds: 30\n          livenessProbe:\n            exec:\n              command: [\"python3\", \"-c\", \"from backend.gpu.device import get_device_info; raise SystemExit(0 if get_device_info().cuda_available else 1)\"]\n            initialDelaySeconds: 60\n            periodSeconds: 60\n      volumes:\n        - name: runtime\n          persistentVolumeClaim:\n            claimName: civiceye-gpu-worker-runtime\n        - name: model-artifacts\n          persistentVolumeClaim:\n            claimName: civiceye-model-artifacts",
    "remediation": null
  },
  {
    "name": "helm_civiceye_template",
    "status": "ok",
    "detail": " app: civiceye-inference-cpu\nspec:\n  replicas: 2\n  selector:\n    matchLabels:\n      app: civiceye-inference-cpu\n  template:\n    metadata:\n      labels:\n        app: civiceye-inference-cpu\n    spec:\n      containers:\n        - name: worker\n          image: \"ghcr.io/civiceye/civiceye-ai-backend:latest\"\n          command: [\"python3\", \"-m\", \"backend.distributed.worker\"]\n          envFrom:\n            - configMapRef:\n                name: civiceye-runtime-config\n          env:\n            - name: CIVICEYE_QUEUE_NAME\n              value: \"cpu.standard\"\n            - name: CIVICEYE_WORKER_ID\n              valueFrom:\n                fieldRef:\n                  fieldPath: metadata.name\n            - name: DATABASE_URL\n              valueFrom:\n                secretKeyRef:\n                  name: civiceye-secrets\n                  key: database-url\n            - name: REDIS_URL\n              valueFrom:\n                secretKeyRef:\n                  name: civiceye-secrets\n                  key: redis-url\n            - name: CIVICEYE_WORKER_SHARED_SECRET\n              valueFrom:\n                secretKeyRef:\n                  name: civiceye-secrets\n                  key: worker-shared-secret\n          readinessProbe:\n            exec:\n              command: [\"python3\", \"-c\", \"import os; from backend.config import settings; from backend.gpu.device import get_device_info; raise SystemExit(0 if settings.worker_shared_secret and get_device_info() is not None else 1)\"]\n            initialDelaySeconds: 30\n            periodSeconds: 20\n          livenessProbe:\n            exec:\n              command: [\"python3\", \"-c\", \"import os; from backend.config import settings; from backend.gpu.device import get_device_info; raise SystemExit(0 if settings.worker_shared_secret and get_device_info() is not None else 1)\"]\n            initialDelaySeconds: 60\n            periodSeconds: 30\n          volumeMounts:\n            - name: ai-runtime\n              mountPath: /app/runtime/ai\n      volumes:\n        - name: ai-runtime\n          persistentVolumeClaim:\n            claimName: civiceye-runtime-media\n\n---\n# Source: civiceye/templates/api.yaml\napiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata:\n  name: civiceye-api\n  namespace: civiceye\nspec:\n  scaleTargetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: civiceye-api\n  minReplicas: 3\n  maxReplicas: 16\n  metrics:\n    - type: Resource\n      resource:\n        name: cpu\n        target:\n          type: Utilization\n          averageUtilization: 70\n---\n# Source: civiceye/templates/web.yaml\napiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata:\n  name: civiceye-web\n  namespace: civiceye\nspec:\n  scaleTargetRef:\n    apiVersion: apps/v1\n    kind: Deployment\n    name: civiceye-web\n  minReplicas: 3\n  maxReplicas: 12\n  metrics:\n    - type: Resource\n      resource:\n        name: cpu\n        target:\n          type: Utilization\n          averageUtilization: 60\n\n---\n# Source: civiceye/templates/storage-ingress.yaml\napiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: civiceye\n  namespace: civiceye\n  annotations:\n    cert-manager.io/cluster-issuer: \"letsencrypt-prod\"\n    nginx.ingress.kubernetes.io/proxy-body-size: \"1024m\"\n    nginx.ingress.kubernetes.io/proxy-read-timeout: \"3600\"\n    nginx.ingress.kubernetes.io/proxy-send-timeout: \"3600\"\nspec:\n  ingressClassName: \"nginx\"\n  tls:\n    - hosts:\n        - \"civiceye.example.com\"\n        - \"api.civiceye.example.com\"\n      secretName: \"civiceye-tls\"\n  rules:\n    - host: \"civiceye.example.com\"\n      http:\n        paths:\n          - path: /\n            pathType: Prefix\n            backend:\n              service:\n                name: civiceye-web\n                port:\n                  number: 3000\n    - host: \"api.civiceye.example.com\"\n      http:\n        paths:\n          - path: /\n            pathType: Prefix\n            backend:\n              service:\n                name: civiceye-api\n                port:\n                  number: 8000",
    "remediation": null
  },
  {
    "name": "postgres_tcp_probe",
    "status": "ok",
    "detail": "TCP connection to localhost:5432 succeeded.",
    "remediation": null
  },
  {
    "name": "redis_tcp_probe",
    "status": "ok",
    "detail": "TCP connection to localhost:6379 succeeded.",
    "remediation": null
  },
  {
    "name": "backend_runtime_diagnostics",
    "status": "failed",
    "detail": "{\n  \"status\": \"failed\",\n  \"service\": \"CivicEye AI Backend\",\n  \"api_version\": \"2.0.0\",\n  \"checks\": [\n    {\n      \"name\": \"environment\",\n      \"status\": \"ok\",\n      \"required\": true,\n      \"detail\": \"Required runtime environment is present.\",\n      \"remediation\": null,\n      \"metadata\": null\n    },\n    {\n      \"name\": \"ai_model_artifact\",\n      \"status\": \"ok\",\n      \"required\": true,\n      \"detail\": \"YOLO weights are present.\",\n      \"remediation\": null,\n      \"metadata\": {\n        \"weights_path\": \"C:\\\\Users\\\\AKILA\\\\Documents\\\\Codex\\\\2026-05-15\\\\you-are-now-acting-as-principal\\\\ai\\\\checkpoints\\\\best.pt\",\n        \"loaded\": false\n      }\n    },\n    {\n      \"name\": \"media_storage\",\n      \"status\": \"ok\",\n      \"required\": true,\n      \"detail\": \"Runtime storage directory is writable.\",\n      \"remediation\": null,\n      \"metadata\": {\n        \"storage_dir\": \"C:\\\\Users\\\\AKILA\\\\Documents\\\\Codex\\\\2026-05-15\\\\you-are-now-acting-as-principal\\\\runtime\\\\ai\"\n      }\n    },\n    {\n      \"name\": \"postgres_postgis\",\n      \"status\": \"failed\",\n      \"required\": true,\n      \"detail\": \"Postgres connection failed after 1 attempts: \",\n      \"remediation\": \"Set DATABASE_URL and run Prisma migrations against a PostGIS-enabled database.\",\n      \"metadata\": null\n    },\n    {\n      \"name\": \"redis\",\n      \"status\": \"failed\",\n      \"required\": true,\n      \"detail\": \"Redis validation failed: Timeout reading from localhost:6379\",\n      \"remediation\": \"Verify Redis is reachable and supports persistence for queue reliability.\",\n      \"metadata\": null\n    },\n    {\n      \"name\": \"distributed_queue\",\n      \"status\": \"failed\",\n      \"required\": true,\n      \"detail\": \"Distributed queue validation failed: Postgres connection failed after 1 attempts: \",\n      \"remediation\": \"Verify migrations are applied and Redis stream access is available.\",\n      \"metadata\": null\n    },\n    {\n      \"name\": \"worker_connectivity\",\n      \"status\": \"failed\",\n      \"required\": false,\n      \"detail\": \"Worker topology validation failed: Postgres connection failed after 1 attempts: \",\n      \"remediation\": \"Verify the distributed inference migration and worker heartbeat table.\",\n      \"metadata\": null\n    },\n    {\n      \"name\": \"dead_letter_queue\",\n      \"status\": \"failed\",\n      \"required\": true,\n      \"detail\": \"Dead-letter queue validation failed: Postgres connection failed after 1 attempts: \",\n      \"remediation\": \"Verify inference job migrations and Redis DLQ stream access.\",\n      \"metadata\": null\n    },\n    {\n      \"name\": \"websocket\",\n      \"status\": \"ok\",\n      \"required\": true,\n      \"detail\": \"Websocket operation bus is initialized.\",\n      \"remediation\": null,\n      \"metadata\": {\n        \"connected_clients\": 0,\n        \"events_published\": 0,\n        \"last_event_at\": null,\n        \"redis_events\": 0,\n        \"local_events\": 0,\n        \"dedupe_window\": 0,\n        \"region\": \"local\",\n        \"node_id\": \"local-api\",\n        \"regional_clients\": {\n          \"local\": 0\n        }\n      }\n    },\n    {\n      \"name\": \"worker_auth\",\n      \"status\": \"ok\",\n      \"required\": true,\n      \"detail\": \"Worker registration signatures are configured.\",\n      \"remediation\": null,\n      \"metadata\": null\n    },\n    {\n      \"name\": \"cloud_gpu_deployment\",\n      \"status\": \"ok\",\n      \"required\": true,\n      \"detail\": \"GPU worker deployment assets and probes are present.\",\n      \"remediation\": null,\n      \"metadata\": null\n    },\n    {\n      \"name\": \"provider_gpu_deployment\",\n      \"status\": \"ok\",\n      \"required\": true,\n      \"detail\": \"Provider deployment scripts and GPU worker docs are present.\",\n      \"remediation\": null,\n      \"metadata\": {\n        \"providers\": [\n          \"aws\",\n          \"azure\",\n          \"gcp\",\n          \"lambda\",\n          \"runpod\",\n          \"vast\"\n        ]\n      }\n    }\n  ],\n  \"gpu\": {\n    \"device\": \"cpu\",\n    \"cuda_available\": false,\n    \"gpu_name\": null,\n    \"half_precision\": false,\n    \"vram_used_mb\": null,\n    \"vram_total_mb\": null\n  },\n  \"model\": {\n    \"model_version\": \"pothole-yolov8-v0.2.0\",\n    \"weights_path\": \"C:\\\\Users\\\\AKILA\\\\Documents\\\\Codex\\\\2026-05-15\\\\you-are-now-acting-as-principal\\\\ai\\\\checkpoints\\\\best.pt\",\n    \"loaded\": false,\n    \"device\": \"cpu\",\n    \"cuda_available\": false,\n    \"gpu_name\": null,\n    \"half_precision\": false,\n    \"vram_used_mb\": null,\n    \"vram_total_mb\": null\n  }\n}",
    "remediation": null
  },
  {
    "name": "distributed_topology",
    "status": "failed",
    "detail": "Postgres connection failed after 1 attempts: ",
    "remediation": "Apply migrations and ensure Postgres is reachable before validating distributed topology."
  },
  {
    "name": "distributed_queue_integrity",
    "status": "failed",
    "detail": "Postgres connection failed after 1 attempts: ",
    "remediation": null
  }
]

## Diagnostics
{
  "status": "failed",
  "service": "CivicEye AI Backend",
  "api_version": "2.0.0",
  "checks": [
    {
      "name": "environment",
      "status": "ok",
      "required": true,
      "detail": "Required runtime environment is present.",
      "remediation": null,
      "metadata": null
    },
    {
      "name": "ai_model_artifact",
      "status": "ok",
      "required": true,
      "detail": "YOLO weights are present.",
      "remediation": null,
      "metadata": {
        "weights_path": "C:\\Users\\AKILA\\Documents\\Codex\\2026-05-15\\you-are-now-acting-as-principal\\ai\\checkpoints\\best.pt",
        "loaded": false
      }
    },
    {
      "name": "media_storage",
      "status": "ok",
      "required": true,
      "detail": "Runtime storage directory is writable.",
      "remediation": null,
      "metadata": {
        "storage_dir": "C:\\Users\\AKILA\\Documents\\Codex\\2026-05-15\\you-are-now-acting-as-principal\\runtime\\ai"
      }
    },
    {
      "name": "postgres_postgis",
      "status": "failed",
      "required": true,
      "detail": "Postgres connection failed after 1 attempts: ",
      "remediation": "Set DATABASE_URL and run Prisma migrations against a PostGIS-enabled database.",
      "metadata": null
    },
    {
      "name": "redis",
      "status": "failed",
      "required": true,
      "detail": "Redis validation failed: Timeout reading from localhost:6379",
      "remediation": "Verify Redis is reachable and supports persistence for queue reliability.",
      "metadata": null
    },
    {
      "name": "distributed_queue",
      "status": "failed",
      "required": true,
      "detail": "Distributed queue validation failed: Postgres connection failed after 1 attempts: ",
      "remediation": "Verify migrations are applied and Redis stream access is available.",
      "metadata": null
    },
    {
      "name": "worker_connectivity",
      "status": "failed",
      "required": false,
      "detail": "Worker topology validation failed: Postgres connection failed after 1 attempts: ",
      "remediation": "Verify the distributed inference migration and worker heartbeat table.",
      "metadata": null
    },
    {
      "name": "dead_letter_queue",
      "status": "failed",
      "required": true,
      "detail": "Dead-letter queue validation failed: Postgres connection failed after 1 attempts: ",
      "remediation": "Verify inference job migrations and Redis DLQ stream access.",
      "metadata": null
    },
    {
      "name": "websocket",
      "status": "ok",
      "required": true,
      "detail": "Websocket operation bus is initialized.",
      "remediation": null,
      "metadata": {
        "connected_clients": 0,
        "events_published": 0,
        "last_event_at": null,
        "redis_events": 0,
        "local_events": 0,
        "dedupe_window": 0,
        "region": "local",
        "node_id": "local-api",
        "regional_clients": {
          "local": 0
        }
      }
    },
    {
      "name": "worker_auth",
      "status": "ok",
      "required": true,
      "detail": "Worker registration signatures are configured.",
      "remediation": null,
      "metadata": null
    },
    {
      "name": "cloud_gpu_deployment",
      "status": "ok",
      "required": true,
      "detail": "GPU worker deployment assets and probes are present.",
      "remediation": null,
      "metadata": null
    },
    {
      "name": "provider_gpu_deployment",
      "status": "ok",
      "required": true,
      "detail": "Provider deployment scripts and GPU worker docs are present.",
      "remediation": null,
      "metadata": {
        "providers": [
          "aws",
          "azure",
          "gcp",
          "lambda",
          "runpod",
          "vast"
        ]
      }
    }
  ],
  "gpu": {
    "device": "cpu",
    "cuda_available": false,
    "gpu_name": null,
    "half_precision": false,
    "vram_used_mb": null,
    "vram_total_mb": null
  },
  "model": {
    "model_version": "pothole-yolov8-v0.2.0",
    "weights_path": "C:\\Users\\AKILA\\Documents\\Codex\\2026-05-15\\you-are-now-acting-as-principal\\ai\\checkpoints\\best.pt",
    "loaded": false,
    "device": "cpu",
    "cuda_available": false,
    "gpu_name": null,
    "half_precision": false,
    "vram_used_mb": null,
    "vram_total_mb": null
  }
}