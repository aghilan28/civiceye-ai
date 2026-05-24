#!/usr/bin/env pwsh
# CivicEye — Dataset Acquisition Launcher (PowerShell)
# Usage: .\ai\scripts\acquire_dataset.ps1 -ApiKey "your_key_here"
#
# Or set env var first and run without -ApiKey:
#   $env:ROBOFLOW_API_KEY = "your_key_here"
#   .\ai\scripts\acquire_dataset.ps1

param(
    [string]$ApiKey       = $env:ROBOFLOW_API_KEY,
    [string]$Workspace    = "smartathon",
    [string]$Project      = "new-pothole-detection",
    [string]$Version      = "",
    [switch]$SkipInstall  = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..\.." ).Path

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  CivicEye — Roboflow Dataset Acquisition" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Root     : $ProjectRoot"
Write-Host "  Workspace: $Workspace"
Write-Host "  Project  : $Project"
Write-Host ""

# ── Validate API key ──────────────────────────────────────────────────────────
if (-not $ApiKey) {
    Write-Error @"
ROBOFLOW_API_KEY is not set.
Set it in one of two ways:

  Option A (PowerShell session):
    `$env:ROBOFLOW_API_KEY = 'paste_your_key_here'
    .\ai\scripts\acquire_dataset.ps1

  Option B (pass as argument):
    .\ai\scripts\acquire_dataset.ps1 -ApiKey 'paste_your_key_here'

Get your key at: https://app.roboflow.com/ → Account → Roboflow API
"@
}

# ── Install dependencies ──────────────────────────────────────────────────────
if (-not $SkipInstall) {
    Write-Host "[1/3] Installing Python dependencies …" -ForegroundColor Yellow
    $ReqFile = Join-Path $ProjectRoot "ai\requirements-acquire.txt"
    if (Test-Path $ReqFile) {
        pip install -r $ReqFile --quiet
    } else {
        pip install roboflow pyyaml tqdm --quiet
    }
    Write-Host "      ✓ Dependencies ready" -ForegroundColor Green
}

# ── Set environment ───────────────────────────────────────────────────────────
$env:ROBOFLOW_API_KEY = $ApiKey
$env:RF_WORKSPACE     = $Workspace
$env:RF_PROJECT       = $Project
if ($Version) { $env:RF_VERSION = $Version }
$env:CIVICEYE_ROOT    = $ProjectRoot

# ── Run acquisition ───────────────────────────────────────────────────────────
Write-Host "[2/3] Running dataset acquisition …" -ForegroundColor Yellow
$Script = Join-Path $ScriptDir "download_roboflow_dataset.py"
python $Script

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌  Acquisition failed. See errors above." -ForegroundColor Red
    exit 1
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/3] Dataset acquisition complete!" -ForegroundColor Green
$DatasetPath = Join-Path $ProjectRoot "ai\datasets\raw\pothole_dataset"
Write-Host "      Path    : $DatasetPath"
Write-Host "      Config  : $DatasetPath\data.yaml"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Ready for YOLOv8 training:" -ForegroundColor Cyan
Write-Host "  yolo detect train data=$DatasetPath\data.yaml model=yolov8n.pt epochs=50 imgsz=640" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
