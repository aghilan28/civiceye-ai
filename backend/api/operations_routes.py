from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, status

from backend.database.postgres import DatabaseUnavailable, postgres_pool
from backend.gis.geospatial import normalize_geo_context, route_segment_key
from backend.incidents.lifecycle import assert_transition
from backend.incidents.severity_engine import SeverityEvidence, classify_incident_severity, repair_priority_for_severity, sla_hours_for_severity
from backend.models.operations import AnalyticsSnapshotResponse, CreateIncidentRequest, IncidentResponse, TransitionIncidentRequest
from backend.security.auth import ROLE_TO_DB_ENUM, Principal, require_permission
from backend.websocket.operations_bus import operation_bus


router = APIRouter(prefix="/api/v1", tags=["civic-operations"])


def enforce_tenant(principal: Principal, municipality_id: str) -> None:
    if principal.role in {"system_admin", "platform_admin"}:
        return
    if principal.municipality_id != municipality_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant access denied")


async def broadcast(event: dict) -> None:
    await operation_bus.broadcast(event)


def row_to_incident(row) -> IncidentResponse:
    return IncidentResponse(
        incident_id=row["id"],
        incident_code=row["incidentCode"],
        municipality_id=row["municipalityId"],
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        road_name=row["roadName"],
        district=row["district_name"],
        city=row["city"],
        state=row["state"],
        postal_code=row["postalCode"],
        geohash=row["geohash"],
        route_segment_id=row["routeSegmentId"],
        severity=row["severity"],
        confidence=float(row["confidence"]),
        status=row["status"],
        assigned_department=row["department_type"],
        repair_priority=row["repairPriority"],
        sla_due_at=row["slaDueAt"],
        detected_at=row["detectedAt"],
        updated_at=row["updatedAt"],
    )


@router.websocket("/operations/events")
async def operations_events(websocket: WebSocket) -> None:
    session_id = await operation_bus.connect(websocket)
    if not session_id:
        return
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "ping":
                await websocket.send_json(await operation_bus.heartbeat(session_id))
    finally:
        operation_bus.disconnect(session_id)


@router.get("/operations/incidents", response_model=list[IncidentResponse])
async def list_incidents(
    municipality_id: str = Query(...),
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_permission("incident:read")),
) -> list[IncidentResponse]:
    enforce_tenant(principal, municipality_id)
    where_status = "AND i.status = $2" if status else ""
    params = [municipality_id, status, limit, offset] if status else [municipality_id, limit, offset]
    limit_param = "$3" if status else "$2"
    offset_param = "$4" if status else "$3"
    sql = f"""
        SELECT i.*, d.name AS district_name, dep.type::text AS department_type
        FROM incidents i
        LEFT JOIN districts d ON d.id = i."districtId"
        LEFT JOIN departments dep ON dep.id = i."assignedDepartmentId"
        WHERE i."municipalityId" = $1 {where_status}
        ORDER BY i."repairPriority" DESC, i."detectedAt" DESC
        LIMIT {limit_param} OFFSET {offset_param}
    """
    try:
        async with postgres_pool.acquire() as connection:
            rows = await connection.fetch(sql, *params)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return [row_to_incident(row) for row in rows]


@router.post("/operations/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(
    payload: CreateIncidentRequest,
    principal: Principal = Depends(require_permission("incident:create")),
) -> IncidentResponse:
    geo = normalize_geo_context(payload.geo.model_dump(mode="json"))
    enforce_tenant(principal, geo.municipality_id)
    route_id = geo.route_segment_id or route_segment_key(geo.geohash, geo.road_name)
    severity = classify_incident_severity(
        SeverityEvidence(
            bbox_area_ratio=payload.detection.bbox_area_ratio,
            image_scale=payload.image_scale,
            edge_variance=payload.detection.edge_variance,
            frame_persistence=payload.detection.frame_persistence,
            confidence_values=[payload.detection.confidence],
        )
    )
    detected_at = geo.timestamp
    sla_due_at = detected_at + timedelta(hours=sla_hours_for_severity(severity))
    incident_id = str(uuid4())
    incident_code = f"CE-{detected_at:%Y%m%d}-{incident_id[:8].upper()}"
    priority = repair_priority_for_severity(severity)

    try:
        async with postgres_pool.acquire() as connection:
            async with connection.transaction():
                district_id = await connection.fetchval(
                    "SELECT id FROM districts WHERE \"municipalityId\" = $1 AND (name = $2 OR code = $2) LIMIT 1",
                    geo.municipality_id,
                    geo.district,
                )
                department_id = await connection.fetchval(
                    """
                    SELECT id FROM departments
                    WHERE "municipalityId" = $1 AND type = 'ROADS'
                    ORDER BY "openIncidentCount"::float / GREATEST("activeCrewCount", 1) ASC
                    LIMIT 1
                    """,
                    geo.municipality_id,
                )
                row = await connection.fetchrow(
                    """
                    INSERT INTO incidents (
                        id, "incidentCode", "municipalityId", "districtId", "routeSegmentId", "createdById",
                        "assignedDepartmentId", latitude, longitude, "roadName", city, state, "postalCode",
                        geohash, severity, confidence, status, "detectionSource", "repairPriority", "slaDueAt",
                        "detectedAt", "verifiedAt", "assignedAt", metadata
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6,
                        $7, $8, $9, $10, $11, $12, $13,
                        $14, $15::"IncidentSeverity", $16, 'VERIFIED'::"IncidentStatus", $17::"DetectionSource", $18, $19,
                        $20, $20, CASE WHEN $7 IS NULL THEN NULL ELSE $20 END, $21::jsonb
                    )
                    RETURNING *
                    """,
                    incident_id,
                    incident_code,
                    geo.municipality_id,
                    district_id,
                    route_id,
                    payload.created_by_id or principal.user_id,
                    department_id,
                    geo.latitude,
                    geo.longitude,
                    geo.road_name,
                    geo.city,
                    geo.state,
                    geo.postal_code,
                    geo.geohash,
                    severity,
                    payload.detection.confidence,
                    geo.source,
                    priority,
                    sla_due_at,
                    detected_at,
                    json.dumps(payload.metadata),
                )
                await connection.execute(
                    """
                    INSERT INTO detections (
                        id, "incidentId", "sessionId", "sourceId", "modelVersion", "className", "classId", confidence,
                        severity, "frameIndex", "bboxX1", "bboxY1", "bboxX2", "bboxY2", "bboxWidthRatio",
                        "bboxHeightRatio", "bboxAreaRatio", "edgeVariance", "framePersistence", latitude,
                        longitude, geohash, "capturedAt"
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::"IncidentSeverity", $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23)
                    """,
                    payload.detection.detection_id,
                    incident_id,
                    payload.detection.session_id,
                    payload.detection.source_id,
                    payload.detection.model_version,
                    payload.detection.class_name,
                    payload.detection.class_id,
                    payload.detection.confidence,
                    severity,
                    payload.detection.frame_index,
                    payload.detection.bbox_x1,
                    payload.detection.bbox_y1,
                    payload.detection.bbox_x2,
                    payload.detection.bbox_y2,
                    payload.detection.bbox_width_ratio,
                    payload.detection.bbox_height_ratio,
                    payload.detection.bbox_area_ratio,
                    payload.detection.edge_variance,
                    payload.detection.frame_persistence,
                    geo.latitude,
                    geo.longitude,
                    geo.geohash,
                    detected_at,
                )
                for media in payload.media_assets:
                    await connection.execute(
                        """
                        INSERT INTO media_assets (
                            id, "incidentId", type, "storageProvider", bucket, "objectKey", "publicUrl",
                            "contentType", "sizeBytes", "checksumSha256", width, height, "capturedAt", metadata
                        )
                        VALUES (
                            $1, $2, $3::"MediaAssetType", $4, $5, $6, $7,
                            $8, $9, $10, $11, $12, $13, $14::jsonb
                        )
                        """,
                        str(uuid4()),
                        incident_id,
                        media.type,
                        media.storage_provider,
                        None,
                        media.object_key,
                        media.public_url,
                        media.content_type,
                        media.size_bytes,
                        media.checksum_sha256,
                        media.width,
                        media.height,
                        media.captured_at,
                        json.dumps(media.metadata),
                    )
                if department_id is not None:
                    await connection.execute(
                        """
                        INSERT INTO repair_tasks (id, "incidentId", "departmentId", status, priority, notes, "updatedAt")
                        VALUES ($1, $2, $3, 'QUEUED'::"RepairTaskStatus", $4, $5, now())
                        """,
                        str(uuid4()),
                        incident_id,
                        department_id,
                        priority,
                        "Created automatically from verified AI detection.",
                    )
                    await connection.execute(
                        """
                        UPDATE departments
                        SET "openIncidentCount" = "openIncidentCount" + 1, "updatedAt" = now()
                        WHERE id = $1
                        """,
                        department_id,
                    )
                await connection.execute(
                    """
                    INSERT INTO audit_logs (id, "municipalityId", "incidentId", "actorId", action, "toStatus", metadata)
                    VALUES ($1, $2, $3, $4, 'incident_created', 'VERIFIED'::"IncidentStatus", $5::jsonb)
                    """,
                    str(uuid4()),
                    geo.municipality_id,
                    incident_id,
                    payload.created_by_id or principal.user_id,
                    json.dumps({"severity": severity, "source": geo.source}),
                )
                enriched = await connection.fetchrow(
                    """
                    SELECT i.*, d.name AS district_name, dep.type::text AS department_type
                    FROM incidents i
                    LEFT JOIN districts d ON d.id = i."districtId"
                    LEFT JOIN departments dep ON dep.id = i."assignedDepartmentId"
                    WHERE i.id = $1
                    """,
                    row["id"],
                )
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    response = row_to_incident(enriched)
    await broadcast({"type": "incident_created", "incident": response.model_dump(mode="json")})
    if response.assigned_department:
        await broadcast({"type": "worker_assigned", "incident": response.model_dump(mode="json")})
    return response


@router.patch("/operations/incidents/{incident_id}/status", response_model=IncidentResponse)
async def transition_incident(
    incident_id: str,
    payload: TransitionIncidentRequest,
    principal: Principal = Depends(require_permission("incident:resolve")),
) -> IncidentResponse:
    try:
        async with postgres_pool.acquire() as connection:
            async with connection.transaction():
                current = await connection.fetchrow("SELECT * FROM incidents WHERE id = $1", incident_id)
                if current is None:
                    raise HTTPException(status_code=404, detail="Incident not found")
                enforce_tenant(principal, current["municipalityId"])
                try:
                    assert_transition(current["status"], payload.status)
                except ValueError as exc:
                    raise HTTPException(status_code=409, detail=str(exc)) from exc
                row = await connection.fetchrow(
                    """
                    UPDATE incidents
                    SET status = $2::"IncidentStatus",
                        "updatedAt" = now(),
                        "assignedAt" = CASE WHEN $2 = 'ASSIGNED' THEN COALESCE("assignedAt", now()) ELSE "assignedAt" END,
                        "startedAt" = CASE WHEN $2 = 'IN_PROGRESS' THEN COALESCE("startedAt", now()) ELSE "startedAt" END,
                        "completedAt" = CASE WHEN $2 = 'COMPLETED' THEN COALESCE("completedAt", now()) ELSE "completedAt" END,
                        "reopenedAt" = CASE WHEN $2 = 'REOPENED' THEN now() ELSE "reopenedAt" END
                    WHERE id = $1
                    RETURNING *
                    """,
                    incident_id,
                    payload.status,
                )
                if payload.status == "IN_PROGRESS":
                    await connection.execute(
                        """
                        UPDATE repair_tasks
                        SET status = 'IN_PROGRESS'::"RepairTaskStatus", "startedAt" = COALESCE("startedAt", now()), "updatedAt" = now()
                        WHERE "incidentId" = $1 AND status IN ('QUEUED', 'ACCEPTED', 'EN_ROUTE')
                        """,
                        incident_id,
                    )
                if payload.status == "COMPLETED":
                    await connection.execute(
                        """
                        UPDATE repair_tasks
                        SET status = 'COMPLETED'::"RepairTaskStatus", "completedAt" = COALESCE("completedAt", now()), "updatedAt" = now()
                        WHERE "incidentId" = $1
                        """,
                        incident_id,
                    )
                    if row["assignedDepartmentId"] is not None:
                        await connection.execute(
                            """
                            UPDATE departments
                            SET "openIncidentCount" = GREATEST("openIncidentCount" - 1, 0), "updatedAt" = now()
                            WHERE id = $1
                            """,
                            row["assignedDepartmentId"],
                        )
                await connection.execute(
                    """
                    INSERT INTO audit_logs (id, "municipalityId", "incidentId", "actorId", "actorRole", action, "fromStatus", "toStatus", metadata)
                    VALUES ($1, $2, $3, $4, $5::"UserRole", 'incident_transitioned', $6::"IncidentStatus", $7::"IncidentStatus", $8::jsonb)
                    """,
                    str(uuid4()),
                    row["municipalityId"],
                    incident_id,
                    payload.actor_id or principal.user_id,
                    payload.actor_role or ROLE_TO_DB_ENUM.get(principal.role, "SUPERVISOR"),
                    current["status"],
                    payload.status,
                    json.dumps({**payload.metadata, "message": payload.message}),
                )
                enriched = await connection.fetchrow(
                    """
                    SELECT i.*, d.name AS district_name, dep.type::text AS department_type
                    FROM incidents i
                    LEFT JOIN districts d ON d.id = i."districtId"
                    LEFT JOIN departments dep ON dep.id = i."assignedDepartmentId"
                    WHERE i.id = $1
                    """,
                    incident_id,
                )
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    response = row_to_incident(enriched)
    await broadcast({"type": "incident_updated", "incident": response.model_dump(mode="json")})
    if payload.status == "IN_PROGRESS":
        await broadcast({"type": "repair_started", "incident": response.model_dump(mode="json")})
    if payload.status == "COMPLETED":
        await broadcast({"type": "repair_completed", "incident": response.model_dump(mode="json")})
    return response


@router.get("/operations/analytics", response_model=AnalyticsSnapshotResponse)
async def analytics(
    municipality_id: str = Query(...),
    principal: Principal = Depends(require_permission("analytics:read")),
) -> AnalyticsSnapshotResponse:
    enforce_tenant(principal, municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            severity_rows = await connection.fetch(
                "SELECT severity::text AS severity, count(*)::int AS count FROM incidents WHERE \"municipalityId\" = $1 GROUP BY severity",
                municipality_id,
            )
            active = await connection.fetchval(
                "SELECT count(*)::int FROM incidents WHERE \"municipalityId\" = $1 AND status <> 'COMPLETED'",
                municipality_id,
            )
            completed = await connection.fetchval(
                "SELECT count(*)::int FROM incidents WHERE \"municipalityId\" = $1 AND status = 'COMPLETED'",
                municipality_id,
            )
            total = await connection.fetchval("SELECT count(*)::int FROM incidents WHERE \"municipalityId\" = $1", municipality_id)
            district_rows = await connection.fetch(
                """
                SELECT d.id, d.name, count(i.id)::int AS incident_count,
                       COALESCE(avg(i."repairPriority"), 0)::float AS risk_score
                FROM districts d
                LEFT JOIN incidents i ON i."districtId" = d.id AND i.status <> 'COMPLETED'
                WHERE d."municipalityId" = $1
                GROUP BY d.id, d.name
                ORDER BY risk_score DESC
                """,
                municipality_id,
            )
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    distribution = {row["severity"]: row["count"] for row in severity_rows}
    return AnalyticsSnapshotResponse(
        municipality_id=municipality_id,
        active_incidents=active or 0,
        severity_distribution=distribution,
        repair_completion_rate=(completed or 0) / max(total or 0, 1),
        average_sla_hours=0,
        recurrence_rate=0,
        district_risk=[dict(row) for row in district_rows],
        updated_at=datetime.now(timezone.utc),
    )
