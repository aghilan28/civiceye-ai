-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "public";

-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('CITIZEN', 'FIELD_WORKER', 'SUPERVISOR', 'MUNICIPALITY_ADMIN', 'SYSTEM_ADMIN');

-- CreateEnum
CREATE TYPE "DepartmentType" AS ENUM ('ROADS', 'DRAINAGE', 'UTILITIES', 'SMART_INFRASTRUCTURE');

-- CreateEnum
CREATE TYPE "IncidentStatus" AS ENUM ('DETECTED', 'VERIFIED', 'ASSIGNED', 'IN_PROGRESS', 'TEMPORARY_FIX', 'COMPLETED', 'REOPENED');

-- CreateEnum
CREATE TYPE "IncidentSeverity" AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

-- CreateEnum
CREATE TYPE "DetectionSource" AS ENUM ('BROWSER_GEOLOCATION', 'MOBILE_GPS', 'UPLOADED_METADATA', 'EXIF', 'DASHCAM_GPS', 'MANUAL');

-- CreateEnum
CREATE TYPE "MediaAssetType" AS ENUM ('DETECTION_IMAGE', 'DETECTION_VIDEO', 'ANNOTATED_OUTPUT', 'REPAIR_BEFORE', 'REPAIR_AFTER', 'REPAIR_PROOF');

-- CreateEnum
CREATE TYPE "RepairTaskStatus" AS ENUM ('QUEUED', 'ACCEPTED', 'EN_ROUTE', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED', 'REJECTED');

-- CreateEnum
CREATE TYPE "NotificationStatus" AS ENUM ('QUEUED', 'SENT', 'READ', 'FAILED');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "role" "UserRole" NOT NULL,
    "municipalityId" TEXT,
    "districtId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "municipalities" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "state" TEXT NOT NULL,
    "country" TEXT NOT NULL DEFAULT 'IN',
    "city" TEXT NOT NULL,
    "postalCode" TEXT,
    "boundaryGeoJson" JSONB,
    "timezone" TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "municipalities_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "districts" (
    "id" TEXT NOT NULL,
    "municipalityId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "boundaryGeoJson" JSONB,
    "riskScore" DECIMAL(7,3) NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "districts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "departments" (
    "id" TEXT NOT NULL,
    "municipalityId" TEXT NOT NULL,
    "type" "DepartmentType" NOT NULL,
    "name" TEXT NOT NULL,
    "activeCrewCount" INTEGER NOT NULL DEFAULT 0,
    "openIncidentCount" INTEGER NOT NULL DEFAULT 0,
    "serviceZones" TEXT[],
    "slaLowHours" INTEGER NOT NULL DEFAULT 168,
    "slaMediumHours" INTEGER NOT NULL DEFAULT 72,
    "slaHighHours" INTEGER NOT NULL DEFAULT 24,
    "slaCriticalHours" INTEGER NOT NULL DEFAULT 4,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "departments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "incidents" (
    "id" TEXT NOT NULL,
    "incidentCode" TEXT NOT NULL,
    "municipalityId" TEXT NOT NULL,
    "districtId" TEXT,
    "routeSegmentId" TEXT,
    "createdById" TEXT,
    "assignedDepartmentId" TEXT,
    "latitude" DECIMAL(10,7) NOT NULL,
    "longitude" DECIMAL(10,7) NOT NULL,
    "roadName" TEXT,
    "city" TEXT NOT NULL,
    "state" TEXT NOT NULL,
    "postalCode" TEXT,
    "geohash" TEXT NOT NULL,
    "severity" "IncidentSeverity" NOT NULL,
    "confidence" DECIMAL(6,5) NOT NULL,
    "status" "IncidentStatus" NOT NULL DEFAULT 'DETECTED',
    "detectionSource" "DetectionSource" NOT NULL,
    "repairPriority" INTEGER NOT NULL,
    "slaDueAt" TIMESTAMP(3) NOT NULL,
    "detectedAt" TIMESTAMP(3) NOT NULL,
    "verifiedAt" TIMESTAMP(3),
    "assignedAt" TIMESTAMP(3),
    "startedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),
    "reopenedAt" TIMESTAMP(3),
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "incidents_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "detections" (
    "id" TEXT NOT NULL,
    "incidentId" TEXT,
    "sessionId" TEXT NOT NULL,
    "sourceId" TEXT NOT NULL,
    "modelVersion" TEXT NOT NULL,
    "className" TEXT NOT NULL,
    "classId" INTEGER NOT NULL,
    "confidence" DECIMAL(6,5) NOT NULL,
    "severity" "IncidentSeverity" NOT NULL,
    "frameIndex" INTEGER,
    "bboxX1" DECIMAL(10,4) NOT NULL,
    "bboxY1" DECIMAL(10,4) NOT NULL,
    "bboxX2" DECIMAL(10,4) NOT NULL,
    "bboxY2" DECIMAL(10,4) NOT NULL,
    "bboxWidthRatio" DECIMAL(8,7) NOT NULL,
    "bboxHeightRatio" DECIMAL(8,7) NOT NULL,
    "bboxAreaRatio" DECIMAL(8,7) NOT NULL,
    "edgeVariance" DECIMAL(12,4) NOT NULL,
    "framePersistence" INTEGER NOT NULL DEFAULT 1,
    "latitude" DECIMAL(10,7),
    "longitude" DECIMAL(10,7),
    "geohash" TEXT,
    "capturedAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "detections_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "media_assets" (
    "id" TEXT NOT NULL,
    "incidentId" TEXT,
    "detectionId" TEXT,
    "repairTaskId" TEXT,
    "type" "MediaAssetType" NOT NULL,
    "storageProvider" TEXT NOT NULL,
    "bucket" TEXT,
    "objectKey" TEXT NOT NULL,
    "publicUrl" TEXT,
    "contentType" TEXT NOT NULL,
    "sizeBytes" BIGINT NOT NULL,
    "checksumSha256" TEXT,
    "width" INTEGER,
    "height" INTEGER,
    "capturedAt" TIMESTAMP(3),
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "media_assets_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "repair_tasks" (
    "id" TEXT NOT NULL,
    "incidentId" TEXT NOT NULL,
    "departmentId" TEXT NOT NULL,
    "fieldWorkerId" TEXT,
    "status" "RepairTaskStatus" NOT NULL DEFAULT 'QUEUED',
    "priority" INTEGER NOT NULL,
    "acceptedAt" TIMESTAMP(3),
    "startedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),
    "notes" TEXT,
    "verification" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "repair_tasks_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "field_workers" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "municipalityId" TEXT NOT NULL,
    "districtId" TEXT,
    "departmentId" TEXT NOT NULL,
    "mobileNumber" TEXT,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "currentLatitude" DECIMAL(10,7),
    "currentLongitude" DECIMAL(10,7),
    "lastSeenAt" TIMESTAMP(3),
    "skills" TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "field_workers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "audit_logs" (
    "id" TEXT NOT NULL,
    "municipalityId" TEXT NOT NULL,
    "incidentId" TEXT,
    "actorId" TEXT,
    "actorRole" "UserRole",
    "action" TEXT NOT NULL,
    "fromStatus" "IncidentStatus",
    "toStatus" "IncidentStatus",
    "ipAddress" TEXT,
    "userAgent" TEXT,
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "notifications" (
    "id" TEXT NOT NULL,
    "municipalityId" TEXT NOT NULL,
    "userId" TEXT,
    "incidentId" TEXT,
    "status" "NotificationStatus" NOT NULL DEFAULT 'QUEUED',
    "channel" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "sentAt" TIMESTAMP(3),
    "readAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "notifications_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "telemetry_events" (
    "id" TEXT NOT NULL,
    "municipalityId" TEXT NOT NULL,
    "actorId" TEXT,
    "eventType" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "latencyMs" INTEGER,
    "payload" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "telemetry_events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "analytics_snapshots" (
    "id" TEXT NOT NULL,
    "municipalityId" TEXT NOT NULL,
    "districtId" TEXT,
    "snapshotDate" TIMESTAMP(3) NOT NULL,
    "potholesByDistrict" JSONB NOT NULL,
    "severityDistribution" JSONB NOT NULL,
    "repairCompletionRate" DECIMAL(6,5) NOT NULL,
    "averageSlaHours" DECIMAL(8,3) NOT NULL,
    "recurrenceRate" DECIMAL(6,5) NOT NULL,
    "roadQualityTrends" JSONB NOT NULL,
    "seasonalFailureAnalysis" JSONB NOT NULL,
    "repairEffectiveness" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "analytics_snapshots_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_municipalityId_role_idx" ON "users"("municipalityId", "role");

-- CreateIndex
CREATE INDEX "users_districtId_idx" ON "users"("districtId");

-- CreateIndex
CREATE INDEX "municipalities_state_city_idx" ON "municipalities"("state", "city");

-- CreateIndex
CREATE INDEX "districts_municipalityId_riskScore_idx" ON "districts"("municipalityId", "riskScore");

-- CreateIndex
CREATE UNIQUE INDEX "districts_municipalityId_code_key" ON "districts"("municipalityId", "code");

-- CreateIndex
CREATE INDEX "departments_municipalityId_openIncidentCount_idx" ON "departments"("municipalityId", "openIncidentCount");

-- CreateIndex
CREATE UNIQUE INDEX "departments_municipalityId_type_key" ON "departments"("municipalityId", "type");

-- CreateIndex
CREATE UNIQUE INDEX "incidents_incidentCode_key" ON "incidents"("incidentCode");

-- CreateIndex
CREATE INDEX "incidents_municipalityId_status_severity_idx" ON "incidents"("municipalityId", "status", "severity");

-- CreateIndex
CREATE INDEX "incidents_municipalityId_geohash_idx" ON "incidents"("municipalityId", "geohash");

-- CreateIndex
CREATE INDEX "incidents_districtId_status_idx" ON "incidents"("districtId", "status");

-- CreateIndex
CREATE INDEX "incidents_routeSegmentId_idx" ON "incidents"("routeSegmentId");

-- CreateIndex
CREATE INDEX "incidents_slaDueAt_idx" ON "incidents"("slaDueAt");

-- CreateIndex
CREATE INDEX "detections_incidentId_idx" ON "detections"("incidentId");

-- CreateIndex
CREATE INDEX "detections_sessionId_frameIndex_idx" ON "detections"("sessionId", "frameIndex");

-- CreateIndex
CREATE INDEX "detections_geohash_idx" ON "detections"("geohash");

-- CreateIndex
CREATE INDEX "detections_capturedAt_idx" ON "detections"("capturedAt");

-- CreateIndex
CREATE INDEX "media_assets_incidentId_type_idx" ON "media_assets"("incidentId", "type");

-- CreateIndex
CREATE INDEX "media_assets_detectionId_idx" ON "media_assets"("detectionId");

-- CreateIndex
CREATE INDEX "media_assets_repairTaskId_idx" ON "media_assets"("repairTaskId");

-- CreateIndex
CREATE INDEX "repair_tasks_departmentId_status_priority_idx" ON "repair_tasks"("departmentId", "status", "priority");

-- CreateIndex
CREATE INDEX "repair_tasks_fieldWorkerId_status_idx" ON "repair_tasks"("fieldWorkerId", "status");

-- CreateIndex
CREATE INDEX "repair_tasks_incidentId_idx" ON "repair_tasks"("incidentId");

-- CreateIndex
CREATE UNIQUE INDEX "field_workers_userId_key" ON "field_workers"("userId");

-- CreateIndex
CREATE INDEX "field_workers_municipalityId_active_idx" ON "field_workers"("municipalityId", "active");

-- CreateIndex
CREATE INDEX "field_workers_departmentId_active_idx" ON "field_workers"("departmentId", "active");

-- CreateIndex
CREATE INDEX "audit_logs_municipalityId_createdAt_idx" ON "audit_logs"("municipalityId", "createdAt");

-- CreateIndex
CREATE INDEX "audit_logs_incidentId_createdAt_idx" ON "audit_logs"("incidentId", "createdAt");

-- CreateIndex
CREATE INDEX "audit_logs_actorId_createdAt_idx" ON "audit_logs"("actorId", "createdAt");

-- CreateIndex
CREATE INDEX "notifications_municipalityId_status_idx" ON "notifications"("municipalityId", "status");

-- CreateIndex
CREATE INDEX "notifications_userId_readAt_idx" ON "notifications"("userId", "readAt");

-- CreateIndex
CREATE INDEX "notifications_incidentId_idx" ON "notifications"("incidentId");

-- CreateIndex
CREATE INDEX "telemetry_events_municipalityId_eventType_createdAt_idx" ON "telemetry_events"("municipalityId", "eventType", "createdAt");

-- CreateIndex
CREATE INDEX "telemetry_events_source_createdAt_idx" ON "telemetry_events"("source", "createdAt");

-- CreateIndex
CREATE INDEX "analytics_snapshots_municipalityId_snapshotDate_idx" ON "analytics_snapshots"("municipalityId", "snapshotDate");

-- CreateIndex
CREATE UNIQUE INDEX "analytics_snapshots_municipalityId_districtId_snapshotDate_key" ON "analytics_snapshots"("municipalityId", "districtId", "snapshotDate");

-- AddForeignKey
ALTER TABLE "users" ADD CONSTRAINT "users_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "users" ADD CONSTRAINT "users_districtId_fkey" FOREIGN KEY ("districtId") REFERENCES "districts"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "districts" ADD CONSTRAINT "districts_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "departments" ADD CONSTRAINT "departments_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "incidents" ADD CONSTRAINT "incidents_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "incidents" ADD CONSTRAINT "incidents_districtId_fkey" FOREIGN KEY ("districtId") REFERENCES "districts"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "incidents" ADD CONSTRAINT "incidents_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "incidents" ADD CONSTRAINT "incidents_assignedDepartmentId_fkey" FOREIGN KEY ("assignedDepartmentId") REFERENCES "departments"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "detections" ADD CONSTRAINT "detections_incidentId_fkey" FOREIGN KEY ("incidentId") REFERENCES "incidents"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "media_assets" ADD CONSTRAINT "media_assets_incidentId_fkey" FOREIGN KEY ("incidentId") REFERENCES "incidents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "media_assets" ADD CONSTRAINT "media_assets_detectionId_fkey" FOREIGN KEY ("detectionId") REFERENCES "detections"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "media_assets" ADD CONSTRAINT "media_assets_repairTaskId_fkey" FOREIGN KEY ("repairTaskId") REFERENCES "repair_tasks"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "repair_tasks" ADD CONSTRAINT "repair_tasks_incidentId_fkey" FOREIGN KEY ("incidentId") REFERENCES "incidents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "repair_tasks" ADD CONSTRAINT "repair_tasks_departmentId_fkey" FOREIGN KEY ("departmentId") REFERENCES "departments"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "repair_tasks" ADD CONSTRAINT "repair_tasks_fieldWorkerId_fkey" FOREIGN KEY ("fieldWorkerId") REFERENCES "field_workers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "field_workers" ADD CONSTRAINT "field_workers_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "field_workers" ADD CONSTRAINT "field_workers_districtId_fkey" FOREIGN KEY ("districtId") REFERENCES "districts"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "field_workers" ADD CONSTRAINT "field_workers_departmentId_fkey" FOREIGN KEY ("departmentId") REFERENCES "departments"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "audit_logs" ADD CONSTRAINT "audit_logs_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "audit_logs" ADD CONSTRAINT "audit_logs_incidentId_fkey" FOREIGN KEY ("incidentId") REFERENCES "incidents"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "audit_logs" ADD CONSTRAINT "audit_logs_actorId_fkey" FOREIGN KEY ("actorId") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_incidentId_fkey" FOREIGN KEY ("incidentId") REFERENCES "incidents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "telemetry_events" ADD CONSTRAINT "telemetry_events_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "telemetry_events" ADD CONSTRAINT "telemetry_events_actorId_fkey" FOREIGN KEY ("actorId") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "analytics_snapshots" ADD CONSTRAINT "analytics_snapshots_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;

