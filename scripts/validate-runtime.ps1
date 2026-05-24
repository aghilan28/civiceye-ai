param(
  [switch]$LoadModel,
  [string]$DatabaseUrl = "postgresql://civiceye:civiceye_dev_password@localhost:5432/civiceye",
  [string]$RedisUrl = "redis://localhost:6379/0",
  [string]$WorkerSecret = "runtime-validation-worker-secret-change-in-production"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not $env:DATABASE_URL) {
  $env:DATABASE_URL = $DatabaseUrl
}
if (-not $env:REDIS_URL) {
  $env:REDIS_URL = $RedisUrl
}
if (-not $env:CIVICEYE_WORKER_SHARED_SECRET) {
  $env:CIVICEYE_WORKER_SHARED_SECRET = $WorkerSecret
}

$argsList = @("scripts/runtime_validation.py", "--database-url", $env:DATABASE_URL, "--redis-url", $env:REDIS_URL, "--worker-secret", $env:CIVICEYE_WORKER_SHARED_SECRET)
if ($LoadModel) {
  $argsList += "--load-model"
  $env:CIVICEYE_VALIDATE_MODEL_LOAD = "1"
}

python @argsList
