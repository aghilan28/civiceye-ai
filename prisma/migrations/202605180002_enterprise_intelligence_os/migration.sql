ALTER TYPE "UserRole" ADD VALUE IF NOT EXISTS 'CONTRACTOR';
ALTER TYPE "UserRole" ADD VALUE IF NOT EXISTS 'EMERGENCY_OPERATOR';

CREATE TYPE "InfrastructureAssetType" AS ENUM ('ROAD', 'BRIDGE', 'DRAINAGE', 'TRAFFIC_SIGNAL', 'STREETLIGHT', 'UTILITY_CORRIDOR');
CREATE TYPE "AIModelType" AS ENUM ('POTHOLE', 'ROAD_CRACK', 'FLOODING', 'GARBAGE_OVERFLOW', 'FALLEN_TREE', 'STREETLIGHT_FAILURE', 'DRAINAGE_BLOCKAGE', 'TRAFFIC_SIGNAL_FAILURE', 'ROAD_EROSION', 'INFRASTRUCTURE_COLLAPSE');
CREATE TYPE "AIModelDeploymentTarget" AS ENUM ('CLOUD_GPU', 'CLOUD_CPU', 'EDGE_JETSON_NANO', 'EDGE_JETSON_XAVIER', 'EDGE_CORAL_TPU', 'VEHICLE_DASHCAM');
CREATE TYPE "InferenceJobStatus" AS ENUM ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED');
CREATE TYPE "EdgeDeviceStatus" AS ENUM ('ONLINE', 'DEGRADED', 'OFFLINE', 'SYNCING');
CREATE TYPE "EmergencySeverity" AS ENUM ('WATCH', 'ELEVATED', 'SEVERE', 'DISASTER');

CREATE TABLE "infrastructure_assets" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "districtId" TEXT,
  "assetType" "InfrastructureAssetType" NOT NULL,
  "assetCode" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "geometryGeoJson" JSONB NOT NULL,
  "conditionScore" DECIMAL(7,3) NOT NULL DEFAULT 100,
  "riskScore" DECIMAL(7,3) NOT NULL DEFAULT 0,
  "lastInspectedAt" TIMESTAMP(3),
  "metadata" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "infrastructure_assets_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "knowledge_graph_edges" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "fromIncidentId" TEXT,
  "toIncidentId" TEXT,
  "fromAssetId" TEXT,
  "toAssetId" TEXT,
  "relationship" TEXT NOT NULL,
  "weight" DECIMAL(8,5) NOT NULL DEFAULT 1,
  "evidence" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "knowledge_graph_edges_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "ai_model_registry" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT,
  "modelType" "AIModelType" NOT NULL,
  "version" TEXT NOT NULL,
  "artifactUri" TEXT NOT NULL,
  "metrics" JSONB NOT NULL,
  "trainingMetadata" JSONB NOT NULL,
  "supportedClasses" TEXT[],
  "deploymentTarget" "AIModelDeploymentTarget" NOT NULL,
  "latencyP50Ms" INTEGER NOT NULL,
  "latencyP95Ms" INTEGER NOT NULL,
  "gpuRequired" BOOLEAN NOT NULL DEFAULT false,
  "edgeCompatible" BOOLEAN NOT NULL DEFAULT false,
  "active" BOOLEAN NOT NULL DEFAULT false,
  "promotedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "ai_model_registry_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "inference_jobs" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "incidentId" TEXT,
  "modelId" TEXT NOT NULL,
  "sourceUri" TEXT NOT NULL,
  "status" "InferenceJobStatus" NOT NULL DEFAULT 'QUEUED',
  "queueName" TEXT NOT NULL,
  "workerId" TEXT,
  "gpuDevice" TEXT,
  "priority" INTEGER NOT NULL DEFAULT 50,
  "attempts" INTEGER NOT NULL DEFAULT 0,
  "latencyMs" INTEGER,
  "result" JSONB NOT NULL DEFAULT '{}',
  "error" TEXT,
  "scheduledAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "startedAt" TIMESTAMP(3),
  "completedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "inference_jobs_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "edge_devices" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "deviceCode" TEXT NOT NULL,
  "deviceType" TEXT NOT NULL,
  "status" "EdgeDeviceStatus" NOT NULL DEFAULT 'OFFLINE',
  "latitude" DECIMAL(10,7),
  "longitude" DECIMAL(10,7),
  "supportedModels" TEXT[],
  "lastSeenAt" TIMESTAMP(3),
  "bandwidthKbps" INTEGER,
  "batteryPercent" INTEGER,
  "syncCursor" TEXT,
  "metadata" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "edge_devices_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "worker_telemetry_events" (
  "id" TEXT NOT NULL,
  "fieldWorkerId" TEXT NOT NULL,
  "latitude" DECIMAL(10,7) NOT NULL,
  "longitude" DECIMAL(10,7) NOT NULL,
  "speedKph" DECIMAL(7,3),
  "headingDegrees" DECIMAL(7,3),
  "batteryPercent" INTEGER,
  "capturedAt" TIMESTAMP(3) NOT NULL,
  "payload" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "worker_telemetry_events_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "agent_decisions" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "incidentId" TEXT,
  "actorId" TEXT,
  "agentName" TEXT NOT NULL,
  "decisionType" TEXT NOT NULL,
  "recommendation" JSONB NOT NULL,
  "confidence" DECIMAL(6,5) NOT NULL,
  "accepted" BOOLEAN,
  "trace" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "agent_decisions_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "prediction_snapshots" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "districtId" TEXT,
  "incidentId" TEXT,
  "assetId" TEXT,
  "predictionType" TEXT NOT NULL,
  "probability" DECIMAL(6,5) NOT NULL,
  "horizonHours" INTEGER NOT NULL,
  "factors" JSONB NOT NULL,
  "modelVersion" TEXT NOT NULL,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "prediction_snapshots_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "emergency_events" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "districtId" TEXT,
  "incidentId" TEXT,
  "eventType" TEXT NOT NULL,
  "severity" "EmergencySeverity" NOT NULL,
  "status" TEXT NOT NULL,
  "centroidLat" DECIMAL(10,7),
  "centroidLng" DECIMAL(10,7),
  "impactRadiusMeters" INTEGER,
  "commandLog" JSONB NOT NULL DEFAULT '[]',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "emergency_events_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "model_drift_events" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "modelId" TEXT NOT NULL,
  "driftType" TEXT NOT NULL,
  "score" DECIMAL(8,5) NOT NULL,
  "threshold" DECIMAL(8,5) NOT NULL,
  "windowStart" TIMESTAMP(3) NOT NULL,
  "windowEnd" TIMESTAMP(3) NOT NULL,
  "evidence" JSONB NOT NULL,
  "resolvedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "model_drift_events_pkey" PRIMARY KEY ("id")
);

ALTER TABLE "detections" ADD COLUMN IF NOT EXISTS "inferenceJobId" TEXT;

CREATE UNIQUE INDEX "infrastructure_assets_municipalityId_assetCode_key" ON "infrastructure_assets"("municipalityId", "assetCode");
CREATE UNIQUE INDEX "ai_model_registry_municipalityId_modelType_version_key" ON "ai_model_registry"("municipalityId", "modelType", "version");
CREATE UNIQUE INDEX "edge_devices_municipalityId_deviceCode_key" ON "edge_devices"("municipalityId", "deviceCode");

CREATE INDEX "infrastructure_assets_municipalityId_assetType_riskScore_idx" ON "infrastructure_assets"("municipalityId", "assetType", "riskScore");
CREATE INDEX "infrastructure_assets_districtId_riskScore_idx" ON "infrastructure_assets"("districtId", "riskScore");
CREATE INDEX "knowledge_graph_edges_municipalityId_relationship_idx" ON "knowledge_graph_edges"("municipalityId", "relationship");
CREATE INDEX "knowledge_graph_edges_fromIncidentId_idx" ON "knowledge_graph_edges"("fromIncidentId");
CREATE INDEX "knowledge_graph_edges_toIncidentId_idx" ON "knowledge_graph_edges"("toIncidentId");
CREATE INDEX "knowledge_graph_edges_fromAssetId_idx" ON "knowledge_graph_edges"("fromAssetId");
CREATE INDEX "knowledge_graph_edges_toAssetId_idx" ON "knowledge_graph_edges"("toAssetId");
CREATE INDEX "ai_model_registry_modelType_active_idx" ON "ai_model_registry"("modelType", "active");
CREATE INDEX "ai_model_registry_deploymentTarget_edgeCompatible_idx" ON "ai_model_registry"("deploymentTarget", "edgeCompatible");
CREATE INDEX "inference_jobs_municipalityId_status_priority_idx" ON "inference_jobs"("municipalityId", "status", "priority");
CREATE INDEX "inference_jobs_queueName_status_idx" ON "inference_jobs"("queueName", "status");
CREATE INDEX "inference_jobs_modelId_status_idx" ON "inference_jobs"("modelId", "status");
CREATE INDEX "edge_devices_municipalityId_status_idx" ON "edge_devices"("municipalityId", "status");
CREATE INDEX "worker_telemetry_events_fieldWorkerId_capturedAt_idx" ON "worker_telemetry_events"("fieldWorkerId", "capturedAt");
CREATE INDEX "agent_decisions_municipalityId_agentName_createdAt_idx" ON "agent_decisions"("municipalityId", "agentName", "createdAt");
CREATE INDEX "agent_decisions_incidentId_idx" ON "agent_decisions"("incidentId");
CREATE INDEX "prediction_snapshots_municipalityId_predictionType_createdAt_idx" ON "prediction_snapshots"("municipalityId", "predictionType", "createdAt");
CREATE INDEX "prediction_snapshots_districtId_predictionType_idx" ON "prediction_snapshots"("districtId", "predictionType");
CREATE INDEX "prediction_snapshots_assetId_idx" ON "prediction_snapshots"("assetId");
CREATE INDEX "emergency_events_municipalityId_severity_status_idx" ON "emergency_events"("municipalityId", "severity", "status");
CREATE INDEX "emergency_events_districtId_status_idx" ON "emergency_events"("districtId", "status");
CREATE INDEX "model_drift_events_municipalityId_driftType_createdAt_idx" ON "model_drift_events"("municipalityId", "driftType", "createdAt");
CREATE INDEX "model_drift_events_modelId_createdAt_idx" ON "model_drift_events"("modelId", "createdAt");
CREATE INDEX "detections_inferenceJobId_idx" ON "detections"("inferenceJobId");

ALTER TABLE "infrastructure_assets" ADD CONSTRAINT "infrastructure_assets_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "infrastructure_assets" ADD CONSTRAINT "infrastructure_assets_districtId_fkey" FOREIGN KEY ("districtId") REFERENCES "districts"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "knowledge_graph_edges" ADD CONSTRAINT "knowledge_graph_edges_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "knowledge_graph_edges" ADD CONSTRAINT "knowledge_graph_edges_fromIncidentId_fkey" FOREIGN KEY ("fromIncidentId") REFERENCES "incidents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "knowledge_graph_edges" ADD CONSTRAINT "knowledge_graph_edges_toIncidentId_fkey" FOREIGN KEY ("toIncidentId") REFERENCES "incidents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "knowledge_graph_edges" ADD CONSTRAINT "knowledge_graph_edges_fromAssetId_fkey" FOREIGN KEY ("fromAssetId") REFERENCES "infrastructure_assets"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "knowledge_graph_edges" ADD CONSTRAINT "knowledge_graph_edges_toAssetId_fkey" FOREIGN KEY ("toAssetId") REFERENCES "infrastructure_assets"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "ai_model_registry" ADD CONSTRAINT "ai_model_registry_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "inference_jobs" ADD CONSTRAINT "inference_jobs_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "inference_jobs" ADD CONSTRAINT "inference_jobs_incidentId_fkey" FOREIGN KEY ("incidentId") REFERENCES "incidents"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "inference_jobs" ADD CONSTRAINT "inference_jobs_modelId_fkey" FOREIGN KEY ("modelId") REFERENCES "ai_model_registry"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE "detections" ADD CONSTRAINT "detections_inferenceJobId_fkey" FOREIGN KEY ("inferenceJobId") REFERENCES "inference_jobs"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "edge_devices" ADD CONSTRAINT "edge_devices_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "worker_telemetry_events" ADD CONSTRAINT "worker_telemetry_events_fieldWorkerId_fkey" FOREIGN KEY ("fieldWorkerId") REFERENCES "field_workers"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "agent_decisions" ADD CONSTRAINT "agent_decisions_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "agent_decisions" ADD CONSTRAINT "agent_decisions_incidentId_fkey" FOREIGN KEY ("incidentId") REFERENCES "incidents"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "agent_decisions" ADD CONSTRAINT "agent_decisions_actorId_fkey" FOREIGN KEY ("actorId") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "prediction_snapshots" ADD CONSTRAINT "prediction_snapshots_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "prediction_snapshots" ADD CONSTRAINT "prediction_snapshots_districtId_fkey" FOREIGN KEY ("districtId") REFERENCES "districts"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "prediction_snapshots" ADD CONSTRAINT "prediction_snapshots_incidentId_fkey" FOREIGN KEY ("incidentId") REFERENCES "incidents"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "prediction_snapshots" ADD CONSTRAINT "prediction_snapshots_assetId_fkey" FOREIGN KEY ("assetId") REFERENCES "infrastructure_assets"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "emergency_events" ADD CONSTRAINT "emergency_events_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "emergency_events" ADD CONSTRAINT "emergency_events_districtId_fkey" FOREIGN KEY ("districtId") REFERENCES "districts"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "emergency_events" ADD CONSTRAINT "emergency_events_incidentId_fkey" FOREIGN KEY ("incidentId") REFERENCES "incidents"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "model_drift_events" ADD CONSTRAINT "model_drift_events_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "model_drift_events" ADD CONSTRAINT "model_drift_events_modelId_fkey" FOREIGN KEY ("modelId") REFERENCES "ai_model_registry"("id") ON DELETE CASCADE ON UPDATE CASCADE;

CREATE INDEX IF NOT EXISTS "idx_incidents_geo_point" ON "incidents" USING GIST (ST_SetSRID(ST_MakePoint(longitude::double precision, latitude::double precision), 4326));
CREATE INDEX IF NOT EXISTS "idx_worker_telemetry_geo_point" ON "worker_telemetry_events" USING GIST (ST_SetSRID(ST_MakePoint(longitude::double precision, latitude::double precision), 4326));
