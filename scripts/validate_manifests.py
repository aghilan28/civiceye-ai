from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required = {
        "api_secrets": ROOT / "deploy/helm/civiceye/templates/api.yaml",
        "api_config": ROOT / "deploy/helm/civiceye/templates/configmap.yaml",
        "gpu_worker": ROOT / "deploy/helm/gpu-worker/templates/deployment.yaml",
        "prometheus": ROOT / "telemetry/prometheus.yml",
    }
    checks: list[dict[str, str]] = []
    failures: list[str] = []
    required_tokens = {
        "api_secrets": ["CIVICEYE_JWT_SECRET", "CIVICEYE_WORKER_SHARED_SECRET", "CIVICEYE_OBJECT_STORAGE_ACCESS_KEY"],
        "api_config": ["CIVICEYE_REQUIRE_AUTH", "CIVICEYE_OBJECT_STORAGE_PROVIDER", "CIVICEYE_WEBSOCKET_MAX_MESSAGES_PER_MINUTE"],
        "gpu_worker": ["nvidia.com/gpu", "readinessProbe", "livenessProbe", "CIVICEYE_WORKER_REPLAY_WINDOW_SECONDS"],
        "prometheus": ["backend-api", "/metrics"],
    }
    for name, path in required.items():
        if not path.exists():
            failures.append(f"{name}: missing {path}")
            continue
        text = path.read_text(encoding="utf-8")
        missing = [token for token in required_tokens[name] if token not in text]
        status = "ok" if not missing else "failed"
        checks.append({"name": name, "status": status, "missing": ",".join(missing)})
        if missing:
            failures.append(f"{name}: missing tokens {missing}")
    report = {"status": "failed" if failures else "ok", "checks": checks, "failures": failures}
    print(json.dumps(report, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
