param(
    [string]$OutputRoot = "results/development/t1_telemetry_native_reference_1m_run1",
    [string]$PythonBin = "D:/Anaconda/envs/.conda/envs/cac/python.exe"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root

if (Test-Path (Join-Path $OutputRoot "preflight_manifest.json")) {
    $preflight = Get-Content (Join-Path $OutputRoot "preflight_manifest.json") -Raw | ConvertFrom-Json
    if ($preflight.status -ne "PASS") { throw "existing T1 preflight is not PASS" }
    Write-Host "Reusing frozen PASS preflight manifest."
} else {
    & $PythonBin scripts/verify_t1_telemetry_native_preflight.py --output-root $OutputRoot --execute
}
& $PythonBin scripts/create_t1_telemetry_native_tape.py --output-root $OutputRoot --execute

foreach ($seed in 2201, 2202, 2203, 2204, 2205) {
    Write-Host "=== T1 UTR-SG seed${seed}: strict continuous 1M ==="
    & $PythonBin scripts/run_t1_telemetry_native_single.py --seed $seed --output-root $OutputRoot --execute `
        2>&1 | Tee-Object -FilePath (Join-Path $OutputRoot "utr_sg_seed$seed.out")
}

Write-Host "=== T1 final-checkpoint telemetry-native evaluation (CPU, one seed at a time) ==="
& $PythonBin scripts/run_t1_telemetry_native_evaluation.py --output-root $OutputRoot --device cpu --execute `
    2>&1 | Tee-Object -FilePath (Join-Path $OutputRoot "t1_evaluation.out")

& $PythonBin scripts/aggregate_t1_telemetry_native_reference.py --output-root $OutputRoot `
    --report-path docs/T1_TELEMETRY_NATIVE_REFERENCE_REPORT.md --execute `
    2>&1 | Tee-Object -FilePath (Join-Path $OutputRoot "t1_aggregate.out")

Write-Host "T1 completed; no extension, comparator, held-out, or canonical work was started."
