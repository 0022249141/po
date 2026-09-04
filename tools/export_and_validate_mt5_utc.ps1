param(
    [string]$Symbol = "XAUUSD_o",
    [int]$BarsDays = 180,
    [int]$TicksDays = 2,
    [string]$Output = "MT5_UTC_EXPORTS"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/2] Exporting canonical MT5 UTC bundle..."
py tools\export_mt5_utc_bundle.py --symbol $Symbol --bars-days $BarsDays --ticks-days $TicksDays --output $Output
if ($LASTEXITCODE -ne 0) {
    throw "MT5 UTC export failed with exit code $LASTEXITCODE"
}

$bundle = Get-ChildItem -Path $Output -Directory |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $bundle) {
    throw "No bundle directory was created under $Output"
}

$manifest = Join-Path $bundle.FullName "binding_manifest.json"
if (-not (Test-Path $manifest)) {
    throw "binding_manifest.json not found in $($bundle.FullName)"
}

Write-Host "[2/2] Validating bundle manifest and hashes..."
py tools\validate_mt5_utc_bundle.py $manifest
if ($LASTEXITCODE -ne 0) {
    throw "MT5 UTC bundle validation failed with exit code $LASTEXITCODE"
}

Write-Host "SUCCESS"
Write-Host "Bundle: $($bundle.FullName)"
Write-Host "Manifest: $manifest"
