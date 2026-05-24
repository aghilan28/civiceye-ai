ALTER TYPE "InfrastructureAssetType" ADD VALUE IF NOT EXISTS 'WASTE_ZONE';
ALTER TYPE "InfrastructureAssetType" ADD VALUE IF NOT EXISTS 'MANHOLE';
ALTER TYPE "InfrastructureAssetType" ADD VALUE IF NOT EXISTS 'EVACUATION_ROUTE';
ALTER TYPE "InfrastructureAssetType" ADD VALUE IF NOT EXISTS 'EMERGENCY_ZONE';

ALTER TYPE "AIModelType" ADD VALUE IF NOT EXISTS 'ILLEGAL_DUMPING';
ALTER TYPE "AIModelType" ADD VALUE IF NOT EXISTS 'LANE_DEGRADATION';
ALTER TYPE "AIModelType" ADD VALUE IF NOT EXISTS 'ROAD_OBSTRUCTION';
ALTER TYPE "AIModelType" ADD VALUE IF NOT EXISTS 'MANHOLE_DAMAGE';

ALTER TYPE "AIModelDeploymentTarget" ADD VALUE IF NOT EXISTS 'AWS_GPU_EC2';
ALTER TYPE "AIModelDeploymentTarget" ADD VALUE IF NOT EXISTS 'GCP_GPU_VM';
ALTER TYPE "AIModelDeploymentTarget" ADD VALUE IF NOT EXISTS 'AZURE_GPU_VM';
ALTER TYPE "AIModelDeploymentTarget" ADD VALUE IF NOT EXISTS 'RUNPOD_GPU';
ALTER TYPE "AIModelDeploymentTarget" ADD VALUE IF NOT EXISTS 'VAST_GPU';
ALTER TYPE "AIModelDeploymentTarget" ADD VALUE IF NOT EXISTS 'LAMBDA_LABS_GPU';
ALTER TYPE "AIModelDeploymentTarget" ADD VALUE IF NOT EXISTS 'EDGE_JETSON_ORIN';
ALTER TYPE "AIModelDeploymentTarget" ADD VALUE IF NOT EXISTS 'EDGE_TFLITE';
ALTER TYPE "AIModelDeploymentTarget" ADD VALUE IF NOT EXISTS 'EDGE_COREML';

ALTER TYPE "InferenceJobStatus" ADD VALUE IF NOT EXISTS 'RETRY';
ALTER TYPE "InferenceJobStatus" ADD VALUE IF NOT EXISTS 'DEAD_LETTER';

DO $$ BEGIN
  CREATE TYPE "TenantPlan" AS ENUM ('STARTER', 'GROWTH', 'ENTERPRISE', 'MISSION_CRITICAL');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE "BillingStatus" AS ENUM ('TRIAL', 'ACTIVE', 'PAST_DUE', 'SUSPENDED', 'CANCELLED');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE "ai_model_registry"
  ADD COLUMN IF NOT EXISTS "rollbackVersion" TEXT,
  ADD COLUMN IF NOT EXISTS "benchmarkProfile" JSONB NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS "deploymentMetadata" JSONB NOT NULL DEFAULT '{}';

ALTER TABLE "inference_jobs"
  ADD COLUMN IF NOT EXISTS "batchKey" TEXT,
  ADD COLUMN IF NOT EXISTS "consensusScore" DECIMAL(6,5),
  ADD COLUMN IF NOT EXISTS "retryAfter" TIMESTAMP(3),
  ADD COLUMN IF NOT EXISTS "deadlineAt" TIMESTAMP(3),
  ADD COLUMN IF NOT EXISTS "telemetry" JSONB NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS "ai_model_audit_trails" (
  "id" TEXT NOT NULL,
  "modelId" TEXT NOT NULL,
  "municipalityId" TEXT,
  "action" TEXT NOT NULL,
  "actorId" TEXT,
  "fromVersion" TEXT,
  "toVersion" TEXT,
  "reason" TEXT NOT NULL,
  "evidence" JSONB NOT NULL DEFAULT '{}',
  "telemetry" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "ai_model_audit_trails_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "billing_accounts" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "plan" "TenantPlan" NOT NULL DEFAULT 'ENTERPRISE',
  "status" "BillingStatus" NOT NULL DEFAULT 'ACTIVE',
  "billingEmail" TEXT,
  "currency" TEXT NOT NULL DEFAULT 'USD',
  "aiUnitPriceUsd" DECIMAL(10,6) NOT NULL DEFAULT 0.0025,
  "storageGbPriceUsd" DECIMAL(10,6) NOT NULL DEFAULT 0.028,
  "infraUnitPriceUsd" DECIMAL(10,6) NOT NULL DEFAULT 0.015,
  "metadata" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "billing_accounts_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "usage_meter_events" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "metric" TEXT NOT NULL,
  "quantity" DECIMAL(14,4) NOT NULL,
  "unit" TEXT NOT NULL,
  "metadata" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "usage_meter_events_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "mobile_sync_events" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT NOT NULL,
  "userId" TEXT,
  "deviceId" TEXT NOT NULL,
  "appRole" "UserRole" NOT NULL,
  "syncDirection" TEXT NOT NULL,
  "offlineSeconds" INTEGER NOT NULL DEFAULT 0,
  "queuedUploads" INTEGER NOT NULL DEFAULT 0,
  "uploadedBytes" BIGINT NOT NULL DEFAULT 0,
  "conflictCount" INTEGER NOT NULL DEFAULT 0,
  "lowBandwidth" BOOLEAN NOT NULL DEFAULT false,
  "websocketSynced" BOOLEAN NOT NULL DEFAULT false,
  "telemetry" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "mobile_sync_events_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "operational_validations" (
  "id" TEXT NOT NULL,
  "municipalityId" TEXT,
  "flowName" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "runtimeChecks" JSONB NOT NULL DEFAULT '{}',
  "deploymentChecks" JSONB NOT NULL DEFAULT '{}',
  "telemetryChecks" JSONB NOT NULL DEFAULT '{}',
  "websocketChecks" JSONB NOT NULL DEFAULT '{}',
  "persistenceChecks" JSONB NOT NULL DEFAULT '{}',
  "scalabilityChecks" JSONB NOT NULL DEFAULT '{}',
  "evidence" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "operational_validations_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "ai_model_audit_trails_modelId_createdAt_idx" ON "ai_model_audit_trails"("modelId", "createdAt");
CREATE INDEX IF NOT EXISTS "ai_model_audit_trails_municipalityId_action_createdAt_idx" ON "ai_model_audit_trails"("municipalityId", "action", "createdAt");
CREATE UNIQUE INDEX IF NOT EXISTS "billing_accounts_municipalityId_key" ON "billing_accounts"("municipalityId");
CREATE INDEX IF NOT EXISTS "billing_accounts_status_plan_idx" ON "billing_accounts"("status", "plan");
CREATE INDEX IF NOT EXISTS "usage_meter_events_municipalityId_metric_createdAt_idx" ON "usage_meter_events"("municipalityId", "metric", "createdAt");
CREATE INDEX IF NOT EXISTS "mobile_sync_events_municipalityId_deviceId_createdAt_idx" ON "mobile_sync_events"("municipalityId", "deviceId", "createdAt");
CREATE INDEX IF NOT EXISTS "mobile_sync_events_userId_createdAt_idx" ON "mobile_sync_events"("userId", "createdAt");
CREATE INDEX IF NOT EXISTS "operational_validations_municipalityId_flowName_createdAt_idx" ON "operational_validations"("municipalityId", "flowName", "createdAt");
CREATE INDEX IF NOT EXISTS "inference_jobs_batchKey_status_idx" ON "inference_jobs"("batchKey", "status");

ALTER TABLE "ai_model_audit_trails" ADD CONSTRAINT "ai_model_audit_trails_modelId_fkey" FOREIGN KEY ("modelId") REFERENCES "ai_model_registry"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "billing_accounts" ADD CONSTRAINT "billing_accounts_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "usage_meter_events" ADD CONSTRAINT "usage_meter_events_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "mobile_sync_events" ADD CONSTRAINT "mobile_sync_events_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "operational_validations" ADD CONSTRAINT "operational_validations_municipalityId_fkey" FOREIGN KEY ("municipalityId") REFERENCES "municipalities"("id") ON DELETE SET NULL ON UPDATE CASCADE;
