from __future__ import annotations

from backend.models.schemas import DeploymentTarget, EdgeDeploymentPlan, EdgeDeploymentRequest, PrecisionMode
from backend.mlops.registry import model_registry


class EdgeDeploymentPlanner:
    def build_plan(self, request: EdgeDeploymentRequest) -> EdgeDeploymentPlan:
        model = model_registry.resolve(request.model_id, request.version)
        blockers: list[str] = []
        if request.target not in model.deployment_targets:
            blockers.append(f"{request.target.value} is not declared as a deployment target for {model.model_id}:{model.version}")
        if request.precision == PrecisionMode.int8 and request.target not in {
            DeploymentTarget.jetson_nano,
            DeploymentTarget.jetson_xavier,
            DeploymentTarget.raspberry_pi_coral,
            DeploymentTarget.low_power_edge,
        }:
            blockers.append("INT8 is reserved for calibrated edge runtimes in this release")
        export_format = self._export_format(request.target)
        telemetry_batch_bytes = max(4096, min(262144, request.uplink_kbps * 64))
        sync_interval_seconds = max(15, min(900, int((request.offline_hours * 3600) / 48)))
        return EdgeDeploymentPlan(
            model_id=model.model_id,
            version=model.version,
            target=request.target,
            export_format=export_format,
            optimization_steps=self._optimization_steps(request.target, request.precision),
            telemetry_batch_bytes=telemetry_batch_bytes,
            sync_interval_seconds=sync_interval_seconds,
            incident_upload_policy="upload compact incident JSON immediately; defer annotated media until bandwidth budget is available",
            state_update_policy="pull signed tenant config and active model manifest on every sync window",
            compatible=not blockers and model.edge_compatible,
            blockers=blockers,
        )

    def _export_format(self, target: DeploymentTarget) -> str:
        if target in {DeploymentTarget.jetson_nano, DeploymentTarget.jetson_xavier, DeploymentTarget.vehicle_mount}:
            return "onnx -> tensorrt_engine"
        if target == DeploymentTarget.raspberry_pi_coral:
            return "onnx -> tflite_edgetpu"
        return "onnxruntime"

    def _optimization_steps(self, target: DeploymentTarget, precision: PrecisionMode) -> list[str]:
        steps = ["export trained weights to ONNX with dynamic batch disabled", "validate exported model against held-out frames"]
        if precision == PrecisionMode.fp16:
            steps.append("build FP16 TensorRT engine when CUDA is available")
        if precision == PrecisionMode.int8:
            steps.extend(["run representative calibration set", "build INT8 engine with calibration cache", "compare INT8 recall against FP32 baseline"])
        if target == DeploymentTarget.raspberry_pi_coral:
            steps.append("compile TensorFlow Lite artifact with Edge TPU compiler")
        steps.extend(["sign artifact manifest", "publish artifact to tenant-scoped edge update channel"])
        return steps


edge_deployment_planner = EdgeDeploymentPlanner()
