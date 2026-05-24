from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4

from asyncpg import Connection

from backend.ai_platform.catalog import MODEL_CATALOG
from backend.ai_platform.orchestrator import ai_orchestrator
from backend.ai_platform.registry import model_registry_service
from backend.config import settings
from backend.distributed.orchestration import distributed_orchestrator
from backend.models.enterprise import (
    AgentRecommendation,
    BillingInvoiceResponse,
    CopilotRequest,
    CopilotResponse,
    CostOptimizationResponse,
    DisasterOverlayResponse,
    EmergencyEventCreate,
    EmergencyEventResponse,
    FieldTaskResponse,
    GraphAnalysisResponse,
    InferenceJobCreate,
    InferenceJobResponse,
    IntelligenceSnapshotResponse,
    MapIncidentFeature,
    MapIntelligenceResponse,
    ModelRegistryCreate,
    ModelRegistryResponse,
    TenantProvisionRequest,
    TenantProvisionResponse,
    UsageMeterRecord,
)
from backend.telemetry.metrics import metrics_store
from backend.websocket.operations_bus import operation_bus


def _json(value):
    if value is None:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    return value


def _row_model(row, model):
    return model(**dict(row))


class EnterpriseIntelligenceService:
    async def map_intelligence(self, connection: Connection, municipality_id: str) -> MapIntelligenceResponse:
        incident_rows = await connection.fetch(
            """
            SELECT i.id AS incident_id, i."incidentCode" AS incident_code, i.latitude, i.longitude,
                   i.severity::text AS severity, i.confidence, i.status::text AS status, m.name AS municipality,
                   d.name AS district, dep.type::text AS assigned_department, i."slaDueAt" AS sla_due_at,
                   i."detectedAt" AS detected_at, i."updatedAt" AS updated_at,
                   COALESCE(jsonb_agg(jsonb_build_object('type', ma.type::text, 'url', ma."publicUrl", 'objectKey', ma."objectKey"))
                     FILTER (WHERE ma.id IS NOT NULL), '[]'::jsonb) AS media
            FROM incidents i
            JOIN municipalities m ON m.id = i."municipalityId"
            LEFT JOIN districts d ON d.id = i."districtId"
            LEFT JOIN departments dep ON dep.id = i."assignedDepartmentId"
            LEFT JOIN media_assets ma ON ma."incidentId" = i.id
            WHERE i."municipalityId" = $1 AND i.status <> 'COMPLETED'
            GROUP BY i.id, m.name, d.name, dep.type
            ORDER BY i."repairPriority" DESC, i."detectedAt" DESC
            LIMIT 750
            """,
            municipality_id,
        )
        district_rows = await connection.fetch(
            """
            SELECT d.id AS district_id, d.name, d."boundaryGeoJson" AS boundary_geojson,
                   count(i.id)::int AS incident_count,
                   count(i.id) FILTER (WHERE i.severity = 'CRITICAL')::int AS critical_count,
                   count(i.id) FILTER (WHERE i."slaDueAt" < now() + interval '6 hours' AND i.status <> 'COMPLETED')::int AS sla_risk_count,
                   LEAST(100, COALESCE(avg(i."repairPriority"), 0) + count(i.id) * 2 + COALESCE(max(d."riskScore"), 0))::float AS degradation_score
            FROM districts d
            LEFT JOIN incidents i ON i."districtId" = d.id AND i.status <> 'COMPLETED'
            WHERE d."municipalityId" = $1
            GROUP BY d.id, d.name, d."boundaryGeoJson"
            ORDER BY degradation_score DESC
            """,
            municipality_id,
        )
        asset_rows = await connection.fetch(
            """
            SELECT id, "assetType"::text AS asset_type, name, "geometryGeoJson" AS geometry_geojson,
                   "conditionScore"::float AS condition_score, "riskScore"::float AS risk_score
            FROM infrastructure_assets
            WHERE "municipalityId" = $1
            ORDER BY "riskScore" DESC
            LIMIT 250
            """,
            municipality_id,
        )
        repair_rows = await connection.fetch(
            """
            SELECT rt.id, rt.status::text AS status, rt.priority, i.id AS incident_id, i."incidentCode" AS incident_code,
                   i.latitude::float AS latitude, i.longitude::float AS longitude, fw.id AS worker_id, u.name AS worker_name
            FROM repair_tasks rt
            JOIN incidents i ON i.id = rt."incidentId"
            LEFT JOIN field_workers fw ON fw.id = rt."fieldWorkerId"
            LEFT JOIN users u ON u.id = fw."userId"
            WHERE i."municipalityId" = $1 AND rt.status IN ('ACCEPTED', 'EN_ROUTE', 'IN_PROGRESS')
            ORDER BY rt.priority DESC
            LIMIT 200
            """,
            municipality_id,
        )
        worker_rows = await connection.fetch(
            """
            SELECT DISTINCT ON (fw.id) fw.id, u.name, wte.latitude::float AS latitude, wte.longitude::float AS longitude,
                   wte."batteryPercent" AS battery_percent, wte."capturedAt" AS captured_at
            FROM field_workers fw
            JOIN users u ON u.id = fw."userId"
            LEFT JOIN worker_telemetry_events wte ON wte."fieldWorkerId" = fw.id
            WHERE fw."municipalityId" = $1 AND fw.active = true
            ORDER BY fw.id, wte."capturedAt" DESC NULLS LAST
            """,
            municipality_id,
        )
        incidents = [MapIncidentFeature(**{**dict(row), "media": _json(row["media"])}) for row in incident_rows]
        heatmap_points = [
            {
                "incident_id": incident.incident_id,
                "coordinates": [incident.longitude, incident.latitude],
                "weight": {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.78, "CRITICAL": 1.0}.get(incident.severity, 0.5) * incident.confidence,
            }
            for incident in incidents
        ]
        return MapIntelligenceResponse(
            municipality_id=municipality_id,
            incidents=incidents,
            districts=[dict(row) for row in district_rows],
            heatmap_points=heatmap_points,
            risk_assets=[dict(row) for row in asset_rows],
            active_repairs=[dict(row) for row in repair_rows],
            worker_telemetry=[dict(row) for row in worker_rows],
            updated_at=datetime.now(timezone.utc),
        )

    async def list_models(self, connection: Connection, municipality_id: str | None) -> list[ModelRegistryResponse]:
        rows = await connection.fetch(
            """
            SELECT id, "municipalityId" AS municipality_id, "modelType"::text AS model_type, version,
                   "artifactUri" AS artifact_uri, metrics, "trainingMetadata" AS training_metadata,
                   "supportedClasses" AS supported_classes, "deploymentTarget"::text AS deployment_target,
                   "latencyP50Ms" AS latency_p50_ms, "latencyP95Ms" AS latency_p95_ms,
                   "gpuRequired" AS gpu_required, "edgeCompatible" AS edge_compatible, active,
                   "promotedAt" AS promoted_at, "createdAt" AS created_at, "updatedAt" AS updated_at
            FROM ai_model_registry
            WHERE ($1::text IS NULL OR "municipalityId" = $1 OR "municipalityId" IS NULL)
            ORDER BY active DESC, "modelType", version DESC
            """,
            municipality_id,
        )
        database_models = [_row_model(row, ModelRegistryResponse) for row in rows]
        runtime_models = model_registry_service.list_models(municipality_id)
        seen = {(model.model_type, model.version, model.municipality_id) for model in database_models}
        database_models.extend(
            model for model in runtime_models if (model.model_type, model.version, model.municipality_id) not in seen
        )
        return database_models

    async def register_model(self, connection: Connection, payload: ModelRegistryCreate) -> ModelRegistryResponse:
        runtime_model = model_registry_service.register(payload)
        if payload.active:
            await connection.execute(
                """
                UPDATE ai_model_registry SET active = false, "updatedAt" = now()
                WHERE "modelType" = $1::"AIModelType" AND ("municipalityId" IS NOT DISTINCT FROM $2)
                """,
                payload.model_type,
                payload.municipality_id,
            )
        row = await connection.fetchrow(
            """
            INSERT INTO ai_model_registry (
              id, "municipalityId", "modelType", version, "artifactUri", metrics, "trainingMetadata",
              "supportedClasses", "deploymentTarget", "latencyP50Ms", "latencyP95Ms", "gpuRequired",
              "edgeCompatible", active, "rollbackVersion", "benchmarkProfile", "deploymentMetadata", "promotedAt", "updatedAt"
            )
            VALUES ($1, $2, $3::"AIModelType", $4, $5, $6::jsonb, $7::jsonb, $8, $9::"AIModelDeploymentTarget",
                    $10, $11, $12, $13, $14, $15, $16::jsonb, $17::jsonb, CASE WHEN $14 THEN now() ELSE NULL END, now())
            RETURNING id, "municipalityId" AS municipality_id, "modelType"::text AS model_type, version,
                      "artifactUri" AS artifact_uri, metrics, "trainingMetadata" AS training_metadata,
                      "supportedClasses" AS supported_classes, "deploymentTarget"::text AS deployment_target,
                      "latencyP50Ms" AS latency_p50_ms, "latencyP95Ms" AS latency_p95_ms,
                      "gpuRequired" AS gpu_required, "edgeCompatible" AS edge_compatible, active,
                      "promotedAt" AS promoted_at, "createdAt" AS created_at, "updatedAt" AS updated_at
            """,
            str(uuid4()),
            payload.municipality_id,
            payload.model_type,
            payload.version,
            payload.artifact_uri,
            json.dumps(payload.metrics),
            json.dumps(payload.training_metadata),
            payload.supported_classes,
            payload.deployment_target,
            payload.latency_p50_ms,
            payload.latency_p95_ms,
            payload.gpu_required,
            payload.edge_compatible,
            payload.active,
            payload.rollback_version,
            json.dumps(payload.benchmark_profile),
            json.dumps(payload.deployment_metadata),
        )
        response = _row_model(row, ModelRegistryResponse) if row else runtime_model
        await connection.execute(
            """
            INSERT INTO ai_model_audit_trails (id, "modelId", "municipalityId", action, "toVersion", reason, evidence, telemetry)
            VALUES ($1, $2, $3, 'register', $4, $5, $6::jsonb, $7::jsonb)
            ON CONFLICT DO NOTHING
            """,
            str(uuid4()),
            row["id"] if row else runtime_model.id,
            payload.municipality_id,
            payload.version,
            "Registered through enterprise model registry API.",
            json.dumps({"metrics": payload.metrics, "supported_classes": payload.supported_classes}),
            json.dumps({"runtime_registry_id": runtime_model.id}),
        )
        await operation_bus.broadcast({"type": "model_registry_updated", "model": response.model_dump(mode="json")})
        return response

    async def enqueue_inference(self, connection: Connection, payload: InferenceJobCreate) -> InferenceJobResponse:
        resolved_model = model_registry_service.resolve_for_request(payload)
        model = await connection.fetchrow(
            """
            SELECT * FROM ai_model_registry
            WHERE "modelType" = $1::"AIModelType" AND active = true
              AND ("municipalityId" = $2 OR "municipalityId" IS NULL)
            ORDER BY "municipalityId" NULLS LAST, "promotedAt" DESC NULLS LAST, "createdAt" DESC
            LIMIT 1
            """,
            payload.model_type,
            payload.municipality_id,
        )
        if model is None:
            model_row = await connection.fetchrow(
                """
                INSERT INTO ai_model_registry (
                  id, "municipalityId", "modelType", version, "artifactUri", metrics, "trainingMetadata",
                  "supportedClasses", "deploymentTarget", "latencyP50Ms", "latencyP95Ms", "gpuRequired",
                  "edgeCompatible", active, "promotedAt", "updatedAt"
                )
                VALUES ($1, $2, $3::"AIModelType", $4, $5, $6::jsonb, $7::jsonb, $8,
                        $9::"AIModelDeploymentTarget", $10, $11, $12, $13, true, now(), now())
                ON CONFLICT ("municipalityId", "modelType", version) DO UPDATE
                SET active = true, "updatedAt" = now()
                RETURNING id
                """,
                str(uuid4()),
                payload.municipality_id,
                resolved_model.model_type,
                resolved_model.version,
                resolved_model.artifact_uri,
                json.dumps(resolved_model.metrics),
                json.dumps(resolved_model.training_metadata),
                resolved_model.supported_classes,
                resolved_model.deployment_target,
                resolved_model.latency_p50_ms,
                resolved_model.latency_p95_ms,
                resolved_model.gpu_required,
                resolved_model.edge_compatible,
            )
            model_id = model_row["id"]
        else:
            model_id = model["id"]
        route = distributed_orchestrator.route_for_job(
            model_type=payload.model_type,
            priority=payload.priority,
            requested_queue=payload.queue_name,
            gpu_required=resolved_model.gpu_required,
        )
        queue_name = route.queue_name
        deadline_at = datetime.now(timezone.utc) + timedelta(seconds=settings.inference_job_timeout_seconds)
        row = await connection.fetchrow(
            """
            INSERT INTO inference_jobs (
              id, "municipalityId", "incidentId", "modelId", "sourceUri", status, "queueName", priority, "batchKey",
              "deadlineAt", telemetry, "updatedAt"
            )
            VALUES ($1, $2, $3, $4, $5, 'QUEUED'::"InferenceJobStatus", $6, $7, $8, $9, $10::jsonb, now())
            RETURNING id, "municipalityId" AS municipality_id, "incidentId" AS incident_id, "modelId" AS model_id,
                      $11::text AS model_type, "sourceUri" AS source_uri, status::text AS status, "queueName" AS queue_name,
                      "batchKey" AS batch_key, priority, attempts, "latencyMs" AS latency_ms, result, error, "scheduledAt" AS scheduled_at,
                      "startedAt" AS started_at, "completedAt" AS completed_at, "createdAt" AS created_at, "updatedAt" AS updated_at
            """,
            str(uuid4()),
            payload.municipality_id,
            payload.incident_id,
            model_id,
            payload.source_uri,
            queue_name,
            payload.priority,
            payload.batch_key,
            deadline_at,
            json.dumps({"route": asdict(route), "requested_models": payload.requested_models, "consensus_required": payload.consensus_required}),
            payload.model_type,
        )
        response = _row_model(row, InferenceJobResponse)
        response = await ai_orchestrator.enqueue(payload, persisted_job=response)
        await distributed_orchestrator.publish_job(response.model_dump(mode="json"))
        queue_counts = await connection.fetch(
            """
            SELECT "queueName" AS queue_name, status::text AS status, count(*)::int AS count
            FROM inference_jobs
            GROUP BY "queueName", status
            """
        )
        for item in queue_counts:
            metrics_store.record_queue(item["status"], item["count"], queue_name=item["queue_name"])
        await operation_bus.broadcast({"type": "AI_detection_received", "job": response.model_dump(mode="json")})
        return response

    async def intelligence_snapshot(self, connection: Connection, municipality_id: str) -> IntelligenceSnapshotResponse:
        active = await connection.fetchval(
            "SELECT count(*)::int FROM incidents WHERE \"municipalityId\" = $1 AND status <> 'COMPLETED'",
            municipality_id,
        )
        overdue = await connection.fetchval(
            "SELECT count(*)::int FROM incidents WHERE \"municipalityId\" = $1 AND status <> 'COMPLETED' AND \"slaDueAt\" < now()",
            municipality_id,
        )
        queue_rows = await connection.fetch(
            "SELECT status::text, count(*)::int AS count FROM inference_jobs WHERE \"municipalityId\" = $1 GROUP BY status",
            municipality_id,
        )
        worker_rows = await connection.fetch(
            """
            SELECT state::text AS state, count(*)::int AS count
            FROM inference_workers
            GROUP BY state
            """
        )
        gpu_rows = await connection.fetch(
            """
            SELECT "workerId" AS worker_id, state::text AS state, "gpuName" AS gpu_name, "vramTotalMb" AS vram_total_mb,
                   "vramUsedMb" AS vram_used_mb, "activeJobCount" AS active_job_count, "lastHeartbeatAt" AS last_heartbeat_at
            FROM inference_workers
            WHERE "gpuCount" > 0
            ORDER BY "lastHeartbeatAt" DESC NULLS LAST
            LIMIT 12
            """
        )
        drift_rows = await connection.fetch(
            """
            SELECT de."driftType" AS drift_type, de.score::float, de.threshold::float, m."modelType"::text AS model_type, de."createdAt" AS created_at
            FROM model_drift_events de
            JOIN ai_model_registry m ON m.id = de."modelId"
            WHERE de."municipalityId" = $1 AND de."resolvedAt" IS NULL
            ORDER BY de."createdAt" DESC
            LIMIT 10
            """,
            municipality_id,
        )
        prediction_rows = await connection.fetch(
            """
            SELECT "predictionType" AS prediction_type, probability::float, "horizonHours" AS horizon_hours, factors, "modelVersion" AS model_version, "createdAt" AS created_at
            FROM prediction_snapshots
            WHERE "municipalityId" = $1
            ORDER BY "createdAt" DESC
            LIMIT 20
            """,
            municipality_id,
        )
        emergency_rows = await connection.fetch(
            """
            SELECT id, "eventType" AS event_type, severity::text, status, "centroidLat"::float AS centroid_lat,
                   "centroidLng"::float AS centroid_lng, "impactRadiusMeters" AS impact_radius_meters, "createdAt" AS created_at
            FROM emergency_events
            WHERE "municipalityId" = $1 AND status <> 'RESOLVED'
            ORDER BY "createdAt" DESC
            LIMIT 20
            """,
            municipality_id,
        )
        recommendations = [
            AgentRecommendation(
                agent_name="Municipal Operations Agent",
                decision_type="sla_workload_balance",
                confidence=0.84 if active else 0.5,
                recommendation={
                    "active_incidents": active or 0,
                    "overdue_incidents": overdue or 0,
                    "action": "increase_roads_crews" if overdue else "maintain_current_dispatch",
                },
                trace={"inputs": ["incidents", "repair_tasks", "sla_due_at"], "policy": "priority_overdue_capacity"},
                reasoning=[
                    "Active incident and overdue SLA counts are the strongest operational pressure signals.",
                    "Crew allocation should track repair priority before lower-severity clustering.",
                ],
                evidence=[{"active_incidents": active or 0, "overdue_incidents": overdue or 0}],
                telemetry_references=["queue_pressure", "websocket_health", "worker_heartbeats"],
                gis_evidence=[{"layer": "district_risk", "municipality_id": municipality_id}],
                incident_correlations=[row["prediction_type"] for row in prediction_rows[:3]],
            )
        ]
        health_penalty = min(70, (active or 0) * 0.45 + (overdue or 0) * 3)
        return IntelligenceSnapshotResponse(
            municipality_id=municipality_id,
            city_health_score=round(max(0, 100 - health_penalty), 2),
            queue_pressure={row["status"]: row["count"] for row in queue_rows},
            gpu_telemetry={
                **ai_orchestrator.telemetry(),
                "source": "worker_heartbeats",
                "available": any(row["state"] == "ONLINE" for row in gpu_rows),
                "workers_by_state": {row["state"]: row["count"] for row in worker_rows},
                "active_jobs": sum(row["count"] for row in queue_rows if row["status"] == "RUNNING"),
                "gpu_workers": [dict(row) for row in gpu_rows],
            },
            websocket_health=operation_bus.health(),
            model_drift=[dict(row) for row in drift_rows],
            agent_recommendations=recommendations,
            predictions=[dict(row) for row in prediction_rows],
            emergency_events=[dict(row) for row in emergency_rows],
            updated_at=datetime.now(timezone.utc),
        )

    async def field_tasks(self, connection: Connection, municipality_id: str, field_worker_id: str | None) -> list[FieldTaskResponse]:
        worker_filter = 'AND ($2::text IS NULL OR rt."fieldWorkerId" = $2)' 
        rows = await connection.fetch(
            f"""
            SELECT rt.id, i.id AS incident_id, i."incidentCode" AS incident_code, rt.status::text AS status,
                   rt.priority, i."roadName" AS road_name, i.latitude::float AS latitude, i.longitude::float AS longitude,
                   i.severity::text AS severity, i."slaDueAt" AS sla_due_at, rt.notes,
                   COALESCE(jsonb_agg(jsonb_build_object('type', ma.type::text, 'url', ma."publicUrl", 'objectKey', ma."objectKey"))
                     FILTER (WHERE ma.id IS NOT NULL AND ma.type = 'REPAIR_BEFORE'), '[]'::jsonb) AS before_media,
                   COALESCE(jsonb_agg(jsonb_build_object('type', ma.type::text, 'url', ma."publicUrl", 'objectKey', ma."objectKey"))
                     FILTER (WHERE ma.id IS NOT NULL AND ma.type IN ('REPAIR_AFTER', 'REPAIR_PROOF')), '[]'::jsonb) AS after_media
            FROM repair_tasks rt
            JOIN incidents i ON i.id = rt."incidentId"
            LEFT JOIN media_assets ma ON ma."repairTaskId" = rt.id
            WHERE i."municipalityId" = $1 {worker_filter}
            GROUP BY rt.id, i.id
            ORDER BY rt.priority DESC, i."slaDueAt" ASC
            LIMIT 200
            """,
            municipality_id,
            field_worker_id,
        )
        return [FieldTaskResponse(**{**dict(row), "before_media": _json(row["before_media"]), "after_media": _json(row["after_media"])}) for row in rows]

    async def create_emergency(self, connection: Connection, payload: EmergencyEventCreate) -> EmergencyEventResponse:
        row = await connection.fetchrow(
            """
            INSERT INTO emergency_events (
              id, "municipalityId", "districtId", "incidentId", "eventType", severity, status,
              "centroidLat", "centroidLng", "impactRadiusMeters", "commandLog", "updatedAt"
            )
            VALUES ($1, $2, $3, $4, $5, $6::"EmergencySeverity", 'ACTIVE', $7, $8, $9, $10::jsonb, now())
            RETURNING id, "municipalityId" AS municipality_id, "districtId" AS district_id, "incidentId" AS incident_id,
                      "eventType" AS event_type, severity::text AS severity, status,
                      "centroidLat"::float AS centroid_lat, "centroidLng"::float AS centroid_lng,
                      "impactRadiusMeters" AS impact_radius_meters, "commandLog" AS command_log,
                      "createdAt" AS created_at, "updatedAt" AS updated_at
            """,
            str(uuid4()),
            payload.municipality_id,
            payload.district_id,
            payload.incident_id,
            payload.event_type,
            payload.severity,
            payload.centroid_lat,
            payload.centroid_lng,
            payload.impact_radius_meters,
            json.dumps(payload.command_log),
        )
        response = _row_model(row, EmergencyEventResponse)
        await operation_bus.broadcast({"type": "emergency_alert", "channel": "emergency", "event": response.model_dump(mode="json")})
        return response

    async def provision_tenant(self, connection: Connection, payload: TenantProvisionRequest) -> TenantProvisionResponse:
        municipality_id = f"MUNI-{uuid4().hex[:10].upper()}"
        admin_user_id = f"USR-{uuid4().hex[:10].upper()}"
        slug = "-".join(payload.municipality_name.lower().replace(",", "").split())[:48] or municipality_id.lower()
        now = datetime.now(timezone.utc)
        async with connection.transaction():
            await connection.execute(
                """
                INSERT INTO municipalities (id, name, state, country, city, "createdAt", "updatedAt")
                VALUES ($1, $2, $3, $4, $5, now(), now())
                """,
                municipality_id,
                payload.municipality_name,
                payload.state,
                payload.country,
                payload.city,
            )
            await connection.execute(
                """
                INSERT INTO users (id, email, name, role, "municipalityId", "createdAt", "updatedAt")
                VALUES ($1, $2, $3, 'MUNICIPALITY_ADMIN'::"UserRole", $4, now(), now())
                """,
                admin_user_id,
                payload.admin_email,
                payload.admin_name,
                municipality_id,
            )
            await connection.execute(
                """
                INSERT INTO billing_accounts (id, "municipalityId", plan, status, "billingEmail", metadata, "updatedAt")
                VALUES ($1, $2, $3::"TenantPlan", 'ACTIVE'::"BillingStatus", $4, $5::jsonb, now())
                """,
                str(uuid4()),
                municipality_id,
                payload.plan,
                payload.billing_email or payload.admin_email,
                json.dumps({"storage_region": payload.storage_region}),
            )
            for model_type in payload.enabled_models or list(MODEL_CATALOG):
                spec = MODEL_CATALOG[model_type]
                await connection.execute(
                    """
                    INSERT INTO ai_model_registry (
                      id, "municipalityId", "modelType", version, "artifactUri", metrics, "trainingMetadata",
                      "supportedClasses", "deploymentTarget", "latencyP50Ms", "latencyP95Ms", "gpuRequired",
                      "edgeCompatible", active, "promotedAt", "updatedAt"
                    )
                    VALUES ($1, $2, $3::"AIModelType", $4, $5, $6::jsonb, $7::jsonb, $8,
                            'CLOUD_GPU'::"AIModelDeploymentTarget", 42, 78, $9, $10, $11, now(), now())
                    ON CONFLICT DO NOTHING
                    """,
                    str(uuid4()),
                    municipality_id,
                    model_type,
                    f"tenant-{model_type.lower()}-v1",
                    "registry://tenant-default",
                    json.dumps({"tenant_seed": True}),
                    json.dumps({"dataset_version": "tenant-bootstrap", "trained_at": now.isoformat()}),
                    [spec.canonical_class],
                    spec.gpu_required,
                    spec.edge_compatible,
                    model_type == "POTHOLE",
                )
        response = TenantProvisionResponse(
            municipality_id=municipality_id,
            tenant_slug=slug,
            admin_user_id=admin_user_id,
            plan=payload.plan,
            isolated_channels=[f"tenant.{municipality_id}.operations", f"tenant.{municipality_id}.emergency", f"tenant.{municipality_id}.ai"],
            storage_namespace=f"tenants/{municipality_id}/{payload.storage_region}",
            ai_config={
                "enabled_models": payload.enabled_models or list(MODEL_CATALOG),
                "thresholds": {key: spec.default_threshold for key, spec in MODEL_CATALOG.items()},
            },
            billing_account={"status": "ACTIVE", "email": payload.billing_email or payload.admin_email},
            created_at=now,
        )
        await operation_bus.broadcast({"type": "tenant_provisioned", "municipality_id": municipality_id, "tenant": response.model_dump(mode="json")})
        return response

    async def meter_usage(self, connection: Connection, payload: UsageMeterRecord) -> dict[str, Any]:
        await connection.execute(
            """
            INSERT INTO usage_meter_events (id, "municipalityId", metric, quantity, unit, metadata)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            """,
            str(uuid4()),
            payload.municipality_id,
            payload.metric,
            payload.quantity,
            payload.unit,
            json.dumps(payload.metadata),
        )
        metrics_store.record_tenant_usage(payload.municipality_id, payload.metric, payload.quantity, payload.unit)
        return {"ok": True, "metered_at": datetime.now(timezone.utc).isoformat()}

    async def invoice(self, connection: Connection, municipality_id: str) -> BillingInvoiceResponse:
        account = await connection.fetchrow(
            "SELECT plan::text, status::text, \"aiUnitPriceUsd\"::float AS ai_price, \"storageGbPriceUsd\"::float AS storage_price, \"infraUnitPriceUsd\"::float AS infra_price FROM billing_accounts WHERE \"municipalityId\" = $1",
            municipality_id,
        )
        if account is None:
            plan = "ENTERPRISE"
            status = "TRIAL"
            ai_price = 0.0025
            storage_price = 0.028
            infra_price = 0.015
        else:
            plan = account["plan"]
            status = account["status"]
            ai_price = account["ai_price"]
            storage_price = account["storage_price"]
            infra_price = account["infra_price"]
        rows = await connection.fetch(
            """
            SELECT metric, unit, sum(quantity)::float AS quantity
            FROM usage_meter_events
            WHERE "municipalityId" = $1 AND "createdAt" >= now() - interval '30 days'
            GROUP BY metric, unit
            """,
            municipality_id,
        )
        usage = [dict(row) for row in rows]
        subtotal = 0.0
        for row in usage:
            metric = row["metric"]
            qty = float(row["quantity"] or 0)
            if "ai" in metric or "inference" in metric:
                subtotal += qty * ai_price
            elif "storage" in metric or "media" in metric:
                subtotal += qty * storage_price
            else:
                subtotal += qty * infra_price
        now = datetime.now(timezone.utc)
        return BillingInvoiceResponse(
            municipality_id=municipality_id,
            plan=plan,
            status=status,
            invoice_id=f"INV-{now:%Y%m}-{municipality_id[-6:]}",
            period_start=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            period_end=now,
            usage=usage,
            subtotal_usd=round(subtotal, 2),
            total_usd=round(subtotal * 1.18, 2),
            generated_at=now,
        )

    async def copilot(self, connection: Connection, payload: CopilotRequest) -> CopilotResponse:
        active = await connection.fetchval("SELECT count(*)::int FROM incidents WHERE \"municipalityId\" = $1 AND status <> 'COMPLETED'", payload.municipality_id)
        overdue = await connection.fetchval(
            "SELECT count(*)::int FROM incidents WHERE \"municipalityId\" = $1 AND status <> 'COMPLETED' AND \"slaDueAt\" < now()",
            payload.municipality_id,
        )
        critical = await connection.fetchval(
            "SELECT count(*)::int FROM incidents WHERE \"municipalityId\" = $1 AND severity = 'CRITICAL' AND status <> 'COMPLETED'",
            payload.municipality_id,
        )
        agents = payload.agent_names or [
            "Incident Analysis Agent",
            "Infrastructure Risk Agent",
            "Emergency Response Agent",
            "Routing Optimization Agent",
            "Municipal Operations Agent",
            "Citizen Experience Agent",
        ]
        recommendations: list[AgentRecommendation] = []
        for agent in agents:
            confidence = 0.91 if critical else 0.78 if overdue else 0.66
            recommendations.append(
                AgentRecommendation(
                    agent_name=agent,
                    decision_type="autonomous_ops_recommendation",
                    confidence=confidence,
                    recommendation={
                        "action": "auto_escalate_and_cluster_repairs" if critical or overdue else "maintain_adaptive_assignment",
                        "active_incidents": active or 0,
                        "critical_incidents": critical or 0,
                        "overdue_incidents": overdue or 0,
                    },
                    trace={"policy": "sla_criticality_capacity", "inputs": ["incidents", "repair_tasks", "district_risk", "websocket_health"]},
                    reasoning=[
                        f"{agent} weighted critical incidents, SLA exposure, and district workload.",
                        "Recommendations include evidence references and confidence to support operator review.",
                    ],
                    evidence=[{"metric": "active_incidents", "value": active or 0}, {"metric": "overdue", "value": overdue or 0}],
                    telemetry_references=["civiceye_inference_latency_ms", "civiceye_queue_depth", "civiceye_websocket_events_total"],
                    gis_evidence=[{"layer": "heatmap", "municipality_id": payload.municipality_id}],
                    incident_correlations=[payload.incident_id] if payload.incident_id else [],
                )
            )
        actions = [
            {"type": "auto_assignment", "enabled": True, "reason": "department queue and severity scoring available"},
            {"type": "sla_breach_prediction", "risk": min(1.0, (overdue or 0) / max(active or 1, 1))},
            {"type": "district_prioritization", "enabled": True, "strategy": "criticality_then_route_density"},
        ]
        return CopilotResponse(
            municipality_id=payload.municipality_id,
            recommendations=recommendations,
            autonomous_actions=actions,
            updated_at=datetime.now(timezone.utc),
        )

    async def graph_analysis(self, connection: Connection, municipality_id: str) -> GraphAnalysisResponse:
        asset_rows = await connection.fetch(
            """
            SELECT id, "assetType"::text AS type, name, "riskScore"::float AS risk_score, "districtId" AS district_id
            FROM infrastructure_assets WHERE "municipalityId" = $1 ORDER BY "riskScore" DESC LIMIT 150
            """,
            municipality_id,
        )
        incident_rows = await connection.fetch(
            """
            SELECT id, severity::text, status::text, "routeSegmentId" AS route_segment_id, "districtId" AS district_id, "repairPriority" AS priority
            FROM incidents WHERE "municipalityId" = $1 AND status <> 'COMPLETED' ORDER BY "repairPriority" DESC LIMIT 250
            """,
            municipality_id,
        )
        edge_rows = await connection.fetch(
            """
            SELECT id, relationship, weight::float, evidence, "fromIncidentId", "toIncidentId", "fromAssetId", "toAssetId"
            FROM knowledge_graph_edges WHERE "municipalityId" = $1 ORDER BY weight DESC LIMIT 500
            """,
            municipality_id,
        )
        nodes = [{"id": row["id"], "kind": "asset", **dict(row)} for row in asset_rows] + [{"id": row["id"], "kind": "incident", **dict(row)} for row in incident_rows]
        edges = [dict(row) for row in edge_rows]
        district_counts: dict[str, int] = {}
        for row in incident_rows:
            district = row["district_id"] or "unassigned"
            district_counts[district] = district_counts.get(district, 0) + 1
        hotspots = [{"district_id": district, "incident_count": count, "score": min(100, count * 8)} for district, count in sorted(district_counts.items(), key=lambda item: item[1], reverse=True)]
        return GraphAnalysisResponse(
            municipality_id=municipality_id,
            nodes=nodes,
            edges=edges,
            cascading_failures=[
                {"root": row["id"], "severity": row["severity"], "propagation_risk": min(1.0, row["priority"] / 100)}
                for row in incident_rows
                if row["severity"] in {"HIGH", "CRITICAL"}
            ],
            hotspots=hotspots,
            dependency_risks=[
                {"asset_id": row["id"], "asset_type": row["type"], "risk_score": row["risk_score"], "dependency": "district_network"}
                for row in asset_rows[:25]
            ],
            updated_at=datetime.now(timezone.utc),
        )

    async def disaster_overlays(self, connection: Connection, municipality_id: str) -> DisasterOverlayResponse:
        emergency_rows = await connection.fetch(
            """
            SELECT id, "eventType" AS event_type, severity::text, "centroidLat"::float AS lat,
                   "centroidLng"::float AS lng, "impactRadiusMeters" AS radius, "districtId" AS district_id
            FROM emergency_events
            WHERE "municipalityId" = $1 AND status <> 'RESOLVED'
            ORDER BY "createdAt" DESC
            """,
            municipality_id,
        )
        district_rows = await connection.fetch(
            """
            SELECT d.id, d.name, d."riskScore"::float AS risk_score, count(i.id)::int AS active_incidents
            FROM districts d
            LEFT JOIN incidents i ON i."districtId" = d.id AND i.status <> 'COMPLETED'
            WHERE d."municipalityId" = $1
            GROUP BY d.id, d.name
            ORDER BY risk_score DESC
            """,
            municipality_id,
        )
        emergencies = [dict(row) for row in emergency_rows]
        return DisasterOverlayResponse(
            municipality_id=municipality_id,
            flood_overlays=[row for row in emergencies if "flood" in str(row["event_type"]).lower()],
            emergency_heatmap=[{"coordinates": [row["lng"], row["lat"]], "weight": 1.0, "event_id": row["id"]} for row in emergencies if row["lat"] is not None and row["lng"] is not None],
            district_scores=[{"district_id": row["id"], "name": row["name"], "score": min(100, row["risk_score"] + row["active_incidents"] * 6)} for row in district_rows],
            evacuation_routes=[{"district_id": row["id"], "route_type": "primary", "status": "available" if row["active_incidents"] < 5 else "congested"} for row in district_rows],
            infrastructure_stress=[{"district_id": row["id"], "stress": min(1.0, (row["risk_score"] + row["active_incidents"]) / 100)} for row in district_rows],
            updated_at=datetime.now(timezone.utc),
        )

    async def cost_optimization(self, connection: Connection, municipality_id: str) -> CostOptimizationResponse:
        queued = await connection.fetchval("SELECT count(*)::int FROM inference_jobs WHERE \"municipalityId\" = $1 AND status IN ('QUEUED','RETRY')", municipality_id)
        media_bytes = await connection.fetchval("SELECT COALESCE(sum(\"sizeBytes\"), 0)::text FROM media_assets ma JOIN incidents i ON i.id = ma.\"incidentId\" WHERE i.\"municipalityId\" = $1", municipality_id)
        active_jobs = await connection.fetchval("SELECT count(*)::int FROM inference_jobs WHERE \"municipalityId\" = $1 AND status = 'RUNNING'", municipality_id)
        storage_gb = int(media_bytes or 0) / (1024**3)
        return CostOptimizationResponse(
            municipality_id=municipality_id,
            gpu_autoscaling={"queued_jobs": queued or 0, "running_jobs": active_jobs or 0, "desired_gpu_workers": min(24, max(1, ((queued or 0) // 25) + 1))},
            spot_capacity={"enabled": True, "providers": ["AWS", "GCP", "Azure", "RunPod", "Vast.ai", "Lambda Labs"], "fallback": "on-demand-gpu"},
            inference_batching={"enabled": True, "target_batch_size": 8 if (queued or 0) > 40 else 4, "adaptive_routing": True},
            storage_lifecycle={"media_gb": round(storage_gb, 4), "archive_after_days": 90, "cold_storage_after_days": 180},
            redis_memory={"policy": "tenant-prefixed-streams-with-ttl", "queue_ttl_hours": 72},
            cdn={"signed_media": True, "compression": ["webp", "h264"], "edge_cache_ttl_seconds": 86400},
            recommendations=[
                {"type": "gpu_autoscaling", "detail": "Scale GPU workers from queue depth and p95 latency."},
                {"type": "media_lifecycle", "detail": "Archive annotated media after active SLA window closes."},
                {"type": "adaptive_inference", "detail": "Route low-priority inspection batches to CPU or spot GPU pools."},
            ],
            updated_at=datetime.now(timezone.utc),
        )


enterprise_intelligence_service = EnterpriseIntelligenceService()
