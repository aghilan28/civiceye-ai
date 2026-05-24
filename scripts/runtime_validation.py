from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ValidationResult:
    name: str
    status: str
    detail: str
    remediation: str | None = None


def run_command(name: str, command: list[str], env: dict[str, str] | None = None, timeout: int = 120) -> ValidationResult:
    resolved = shutil.which(command[0])
    if resolved is None and os.name == "nt":
        resolved = shutil.which(f"{command[0]}.cmd") or shutil.which(f"{command[0]}.exe")
    if resolved is None:
        return ValidationResult(name, "failed", f"Command not found: {command[0]}", "Install the required CLI and rerun validation.")
    try:
        completed = subprocess.run(
            [resolved, *command[1:]],
            cwd=ROOT,
            env={**os.environ, **(env or {})},
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ValidationResult(name, "failed", f"Command timed out after {timeout}s: {' '.join(command)}", "Inspect the command output and service health.")
    output = (completed.stdout + "\n" + completed.stderr).strip()
    detail = output[-4000:] if output else "ok"
    return ValidationResult(name, "ok" if completed.returncode == 0 else "failed", detail)


def validate_files() -> list[ValidationResult]:
    required = [
        "backend/main.py",
        "backend/api/routes.py",
        "backend/api/operations_routes.py",
        "backend/api/enterprise_routes.py",
        "backend/inference/model_loader.py",
        "backend/distributed/worker.py",
        "prisma/schema.prisma",
        "docker-compose.yml",
        "Dockerfile",
        "Dockerfile.backend",
        "Dockerfile.ai",
        "deploy/gpu-worker/docker-compose.gpu-worker.yml",
        "deploy/helm/gpu-worker/Chart.yaml",
        "deploy/gpu-worker/validate-worker-runtime.sh",
        "deploy/kubernetes/civiceye-enterprise.yaml",
        "telemetry/prometheus.yml",
        "ai/checkpoints/best.pt",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    status = "ok" if not missing else "failed"
    detail = "All critical runtime files exist." if not missing else f"Missing: {', '.join(missing)}"
    return [ValidationResult("critical_files", status, detail, "Restore missing runtime files." if missing else None)]


async def validate_backend_runtime(load_model: bool) -> ValidationResult:
    sys.path.insert(0, str(ROOT))
    try:
        from backend.runtime.diagnostics import runtime_diagnostics

        diagnostics = await runtime_diagnostics.collect(include_model_load=load_model)
        return ValidationResult("backend_runtime_diagnostics", diagnostics["status"], json.dumps(diagnostics, indent=2, default=str))
    except Exception as exc:
        return ValidationResult("backend_runtime_diagnostics", "failed", str(exc))


def validate_tooling(database_url: str) -> list[ValidationResult]:
    results = [
        run_command("typescript_typecheck", ["npm", "run", "typecheck"], timeout=180),
        run_command("python_compile", [sys.executable, "-m", "compileall", "backend", "scripts"], timeout=180),
        run_command("prisma_schema", ["npx", "prisma", "validate"], env={"DATABASE_URL": database_url}, timeout=120),
    ]
    if shutil.which("docker"):
        results.append(run_command("docker_engine", ["docker", "version"], timeout=45))
        results.append(run_command("docker_compose_config", ["docker", "compose", "config", "--quiet"], timeout=120))
    else:
        results.append(ValidationResult("docker_engine", "failed", "Docker CLI is not available on PATH."))
        results.append(ValidationResult("docker_compose_config", "failed", "Docker CLI is not available on PATH."))
    if shutil.which("kubectl"):
        results.append(
            run_command(
                "kubernetes_manifest_client_validation",
                ["kubectl", "apply", "--dry-run=client", "--validate=false", "-f", "deploy/kubernetes/civiceye-enterprise.yaml"],
                timeout=45,
            )
        )
    else:
        results.append(ValidationResult("kubernetes_manifest_client_validation", "failed", "kubectl is not available on PATH."))
    if shutil.which("helm"):
        results.append(run_command("helm_gpu_worker_template", ["helm", "template", "civiceye-gpu-worker", "deploy/helm/gpu-worker"], timeout=120))
        results.append(run_command("helm_civiceye_template", ["helm", "template", "civiceye", "deploy/helm/civiceye"], timeout=120))
    else:
        results.append(ValidationResult("helm_template_validation", "failed", "Helm CLI is not available on PATH."))
    return results


async def _bounded(name: str, coro, timeout: float, remediation: str | None = None) -> ValidationResult:
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return ValidationResult(name, "failed", f"Validation timed out after {timeout}s.", remediation)


async def _tcp_probe(name: str, host: str, port: int, timeout: float = 3.0) -> ValidationResult:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        with suppress(Exception):
            await writer.wait_closed()
        return ValidationResult(name, "ok", f"TCP connection to {host}:{port} succeeded.")
    except Exception as exc:
        return ValidationResult(name, "failed", f"TCP connection to {host}:{port} failed: {exc}")


def _write_status_documents(results: list[ValidationResult], diagnostics: dict | None = None) -> dict[str, Path]:
    runtime_dir = ROOT / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "ok" if not any(result.status != "ok" for result in results) else "failed",
        "results": [asdict(result) for result in results],
        "diagnostics": diagnostics or {},
    }
    paths = {
        "LOCAL_RUNTIME_STATUS.md": runtime_dir / "LOCAL_RUNTIME_STATUS.md",
        "DISTRIBUTED_RUNTIME_STATUS.md": runtime_dir / "DISTRIBUTED_RUNTIME_STATUS.md",
        "GPU_DEPLOYMENT_STATUS.md": runtime_dir / "GPU_DEPLOYMENT_STATUS.md",
        "FINAL_RUNTIME_AUDIT.md": runtime_dir / "FINAL_RUNTIME_AUDIT.md",
        "FINAL_PRODUCTION_READINESS.md": runtime_dir / "FINAL_PRODUCTION_READINESS.md",
    }
    for name, path in paths.items():
        path.write_text(
            "\n".join(
                [
                    f"# {name.replace('_', ' ').replace('.md', '')}",
                    "",
                    f"Generated: {status['generated_at']}",
                    f"Overall status: {status['status']}",
                    "",
                    "## Results",
                    json.dumps(status["results"], indent=2, default=str),
                    "",
                    "## Diagnostics",
                    json.dumps(status["diagnostics"], indent=2, default=str),
                ]
            ),
            encoding="utf-8",
        )
    return paths


async def validate_queue_integrity() -> ValidationResult:
    sys.path.insert(0, str(ROOT))
    try:
        from backend.config import settings
        from backend.database.postgres import postgres_pool
        from backend.distributed.redis_client import redis_coordinator

        async with postgres_pool.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT status::text AS status, count(*)::int AS count
                FROM inference_jobs
                GROUP BY status
                """
            )
            orphaned = await connection.fetchval(
                """
                SELECT count(*)::int
                FROM inference_jobs
                WHERE status = 'RUNNING' AND ("workerId" IS NULL OR "deadlineAt" <= now())
                """
            )
        redis_state = {}
        if settings.redis_url:
            async with redis_coordinator.client() as client:
                await redis_coordinator.ensure_consumer_group()
                redis_state = {
                    "stream": await client.xinfo_stream(settings.inference_stream),
                    "groups": await client.xinfo_groups(settings.inference_stream),
                }
        status = "ok" if not orphaned else "failed"
        return ValidationResult(
            "distributed_queue_integrity",
            status,
            json.dumps({"jobs_by_status": [dict(row) for row in rows], "orphaned_running_jobs": orphaned or 0, "redis": redis_state}, indent=2, default=str),
            "Run distributed recovery before deployment." if orphaned else None,
        )
    except Exception as exc:
        return ValidationResult("distributed_queue_integrity", "failed", str(exc))


async def validate_distributed_topology() -> ValidationResult:
    sys.path.insert(0, str(ROOT))
    try:
        from backend.distributed.orchestration import distributed_orchestrator

        topology = await distributed_orchestrator.topology()
        return ValidationResult("distributed_topology", "ok", json.dumps(topology, indent=2, default=str))
    except Exception as exc:
        return ValidationResult(
            "distributed_topology",
            "failed",
            str(exc),
            "Apply migrations and ensure Postgres is reachable before validating distributed topology.",
        )


def write_report(name: str, payload: dict) -> Path:
    reports = ROOT / "runtime" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    path = reports / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


async def main() -> int:
    parser = argparse.ArgumentParser(description="CivicEye production runtime validation")
    parser.add_argument("--load-model", action="store_true", help="Load and warm up the YOLO model during diagnostics.")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql://civiceye:civiceye_dev_password@localhost:5432/civiceye"),
        help="Database URL used for Prisma validation when DATABASE_URL is not already exported.",
    )
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        help="Redis URL used for queue and websocket diagnostics when REDIS_URL is not already exported.",
    )
    parser.add_argument(
        "--jwt-secret",
        default=os.getenv("CIVICEYE_JWT_SECRET", "runtime-validation-local-secret-change-in-production"),
        help="JWT secret used for local diagnostics when CIVICEYE_JWT_SECRET is not already exported.",
    )
    parser.add_argument(
        "--worker-secret",
        default=os.getenv("CIVICEYE_WORKER_SHARED_SECRET", "runtime-validation-worker-secret-change-in-production"),
        help="Worker shared secret used for signed worker diagnostics.",
    )
    args = parser.parse_args()

    os.environ.setdefault("DATABASE_URL", args.database_url)
    os.environ.setdefault("REDIS_URL", args.redis_url)
    os.environ.setdefault("CIVICEYE_JWT_SECRET", args.jwt_secret)
    os.environ.setdefault("CIVICEYE_WORKER_SHARED_SECRET", args.worker_secret)

    results = []
    results.extend(validate_files())
    results.extend(validate_tooling(args.database_url))
    results.append(await _tcp_probe("postgres_tcp_probe", "localhost", 5432))
    results.append(await _tcp_probe("redis_tcp_probe", "localhost", 6379))
    results.append(
        await _bounded(
            "backend_runtime_diagnostics",
            validate_backend_runtime(load_model=args.load_model),
            timeout=45,
            remediation="Verify Postgres, Redis, runtime dependencies, and model artifacts.",
        )
    )
    results.append(
        await _bounded(
            "distributed_topology",
            validate_distributed_topology(),
            timeout=30,
            remediation="Apply migrations and ensure Postgres is reachable before validating distributed topology.",
        )
    )
    results.append(
        await _bounded(
            "distributed_queue_integrity",
            validate_queue_integrity(),
            timeout=30,
            remediation="Ensure Postgres and Redis are reachable and migrations have completed.",
        )
    )
    diagnostics = {}
    try:
        from backend.runtime.diagnostics import runtime_diagnostics

        diagnostics = await asyncio.wait_for(runtime_diagnostics.collect(include_model_load=args.load_model), timeout=45)
    except Exception:
        diagnostics = {}

    failed = [result for result in results if result.status != "ok"]
    report = {
        "status": "failed" if failed else "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": [asdict(result) for result in results],
        "reports": {
            "runtime_audit": "runtime/reports/runtime-audit-report.json",
            "deployment_readiness": "runtime/reports/deployment-readiness-report.json",
            "distributed_topology": "runtime/reports/distributed-topology-report.json",
        },
    }
    write_report("runtime-audit-report.json", report)
    write_report(
        "deployment-readiness-report.json",
        {
            "status": report["status"],
            "checks": [asdict(result) for result in results if result.name in {"docker_compose_config", "kubernetes_manifest_client_validation", "critical_files", "backend_runtime_diagnostics"}],
        },
    )
    topology_result = next((result for result in results if result.name == "distributed_topology"), None)
    write_report(
        "distributed-topology-report.json",
        {
            "status": topology_result.status if topology_result else "failed",
            "detail": topology_result.detail if topology_result else "topology validation did not run",
        },
    )
    _write_status_documents(results, diagnostics)
    print(json.dumps(report, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
