DO $$ BEGIN
  CREATE TYPE "InferenceWorkerState" AS ENUM ('ONLINE', 'DRAINING', 'OFFLINE', 'EXPIRED', 'FAILED');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE "inference_jobs"
  ADD COLUMN IF NOT EXISTS "workerId" TEXT,
  ADD COLUMN IF NOT EXISTS "retryAfter" TIMESTAMP(3),
  ADD COLUMN IF NOT EXISTS "deadlineAt" TIMESTAMP(3),
  ADD COLUMN IF NOT EXISTS "telemetry" JSONB NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS "inference_workers" (
  "id" TEXT NOT NULL,
  "workerId" TEXT NOT NULL,
  "state" "InferenceWorkerState" NOT NULL DEFAULT 'ONLINE',
  "queueNames" TEXT[] NOT NULL DEFAULT '{}',
  "capabilities" JSONB NOT NULL DEFAULT '{}',
  "supportedModels" TEXT[] NOT NULL DEFAULT '{}',
  "supportedClasses" TEXT[] NOT NULL DEFAULT '{}',
  "gpuCount" INTEGER NOT NULL DEFAULT 0,
  "gpuName" TEXT,
  "cudaVersion" TEXT,
  "torchVersion" TEXT,
  "vramTotalMb" INTEGER,
  "vramUsedMb" INTEGER,
  "activeJobCount" INTEGER NOT NULL DEFAULT 0,
  "maxConcurrentJobs" INTEGER NOT NULL DEFAULT 1,
  "lastHeartbeatAt" TIMESTAMP(3),
  "registeredAt" TIMESTAMP(3) NOT NULL,
  "expiresAt" TIMESTAMP(3),
  "failureReason" TEXT,
  "remoteAddress" TEXT,
  "telemetry" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "inference_workers_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "inference_workers_workerId_key" ON "inference_workers"("workerId");
CREATE INDEX IF NOT EXISTS "inference_workers_state_expiresAt_idx" ON "inference_workers"("state", "expiresAt");

CREATE TABLE IF NOT EXISTS "inference_job_events" (
  "id" TEXT NOT NULL,
  "jobId" TEXT NOT NULL,
  "workerId" TEXT,
  "event" TEXT NOT NULL,
  "payload" JSONB NOT NULL DEFAULT '{}',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "inference_job_events_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "inference_job_events_jobId_createdAt_idx" ON "inference_job_events"("jobId", "createdAt");
CREATE INDEX IF NOT EXISTS "inference_job_events_workerId_createdAt_idx" ON "inference_job_events"("workerId", "createdAt");
CREATE INDEX IF NOT EXISTS "inference_jobs_workerId_idx" ON "inference_jobs"("workerId");
CREATE INDEX IF NOT EXISTS "inference_jobs_queueName_status_retryAfter_idx" ON "inference_jobs"("queueName", "status", "retryAfter");

ALTER TABLE "inference_jobs"
  ADD CONSTRAINT "inference_jobs_workerId_fkey" FOREIGN KEY ("workerId") REFERENCES "inference_workers"("workerId") ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "inference_job_events"
  ADD CONSTRAINT "inference_job_events_jobId_fkey" FOREIGN KEY ("jobId") REFERENCES "inference_jobs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "inference_job_events"
  ADD CONSTRAINT "inference_job_events_workerId_fkey" FOREIGN KEY ("workerId") REFERENCES "inference_workers"("workerId") ON DELETE SET NULL ON UPDATE CASCADE;
