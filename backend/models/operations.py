from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


IncidentStatus = Literal["DETECTED", "VERIFIED", "ASSIGNED", "IN_PROGRESS", "TEMPORARY_FIX", "COMPLETED", "REOPENED"]
IncidentSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
DetectionSource = Literal["BROWSER_GEOLOCATION", "MOBILE_GPS", "UPLOADED_METADATA", "EXIF", "DASHCAM_GPS", "MANUAL"]


class GeoMetadata(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timestamp: datetime | None = None
    road_name: str | None = None
    district: str | None = None
    city: str
    state: str
    postal_code: str | None = None
    municipality_id: str
    route_segment_id: str | None = None
    source: DetectionSource = "UPLOADED_METADATA"


class DetectionEvidence(BaseModel):
    detection_id: str
    session_id: str
    source_id: str
    model_version: str
    confidence: float = Field(ge=0, le=1)
    class_id: int
    class_name: str
    frame_index: int | None = None
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    bbox_width_ratio: float = Field(ge=0, le=1)
    bbox_height_ratio: float = Field(ge=0, le=1)
    bbox_area_ratio: float = Field(ge=0, le=1)
    edge_variance: float = Field(ge=0)
    frame_persistence: int = Field(default=1, ge=1)


class MediaAssetInput(BaseModel):
    type: str
    storage_provider: str
    object_key: str
    public_url: str | None = None
    content_type: str
    size_bytes: int = Field(ge=1)
    checksum_sha256: str | None = None
    width: int | None = None
    height: int | None = None
    captured_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateIncidentRequest(BaseModel):
    geo: GeoMetadata
    detection: DetectionEvidence
    media_assets: list[MediaAssetInput] = Field(default_factory=list)
    image_scale: float = Field(default=1.0, ge=0, le=1)
    created_by_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentResponse(BaseModel):
    incident_id: str
    incident_code: str
    municipality_id: str
    latitude: float
    longitude: float
    road_name: str | None
    district: str | None
    city: str
    state: str
    postal_code: str | None
    geohash: str
    route_segment_id: str | None
    severity: IncidentSeverity
    confidence: float
    status: IncidentStatus
    assigned_department: str | None
    repair_priority: int
    sla_due_at: datetime
    detected_at: datetime
    updated_at: datetime


class TransitionIncidentRequest(BaseModel):
    status: IncidentStatus
    actor_id: str | None = None
    actor_role: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepairTaskUpdateRequest(BaseModel):
    status: Literal["QUEUED", "ACCEPTED", "EN_ROUTE", "IN_PROGRESS", "BLOCKED", "COMPLETED", "REJECTED"]
    field_worker_id: str | None = None
    notes: str | None = None
    proof_media_asset_ids: list[str] = Field(default_factory=list)
    verification: dict[str, Any] = Field(default_factory=dict)


class AnalyticsSnapshotResponse(BaseModel):
    municipality_id: str
    active_incidents: int
    severity_distribution: dict[str, int]
    repair_completion_rate: float
    average_sla_hours: float
    recurrence_rate: float
    district_risk: list[dict[str, Any]]
    updated_at: datetime
