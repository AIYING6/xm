param(
    [int]$Updates = 256,
    [int]$ParallelEnvs = 8,
    [string]$OutputRoot = "results/development/pscr_p8_pbrc_development_20260913"
)

$ErrorActionPreference = 'Stop'
$python = 'D:/Anaconda/envs/.conda/envs/cac/python.exe'
$arms = 'plain', 'plan_no_reliability', 'permuted_pbrc', 'pbrc'
$seeds = 97211, 97212, 97213
if (Test-Path $OutputRoot) { throw "Refusing to overwrite $OutputRoot" }
New-Item -ItemType Directory -Force -Path $OutputRoot, (Join-Path $OutputRoot 'logs') | Out-Null

foreach ($arm in $arms) {
    foreach ($seed in $seeds) {
        $run = Join-Path $OutputRoot "runs/$arm/seed$seed"
        Write-Host "[P8 PBRC development] training $arm / $seed"
        & $python scripts/run_pscr_p8_pbrc_development.py train --arm $arm --seed $seed --updates $Updates --parallel-envs $ParallelEnvs --output-root $run --execute 2>&1 |
            Tee-Object -FilePath (Join-Path $OutputRoot "logs/train_${arm}_seed$seed.log")
        if ($LASTEXITCODE -ne 0) { throw "training failed: $arm / $seed" }
    }
}
foreach ($arm in $arms) {
    foreach ($seed in $seeds) {
        $run = Join-Path $OutputRoot "runs/$arm/seed$seed"
        $eval = Join-Path $OutputRoot "evaluations/$arm/seed$seed"
        Write-Host "[P8 PBRC development] evaluating $arm / $seed"
        & $python scripts/run_pscr_p8_pbrc_development.py evaluate --arm $arm --seed ($seed + 1000) --checkpoint (Join-Path $run 'endpoint.pt') --output-root $eval --execute 2>&1 |
            Tee-Object -FilePath (Join-Path $OutputRoot "logs/evaluate_${arm}_seed$seed.log")
        if ($LASTEXITCODE -ne 0) { throw "evaluation failed: $arm / $seed" }
    }
}
& $python scripts/aggregate_pscr_p8_pbrc_development.py --root (Join-Path $OutputRoot 'diagnostics') --execute
if ($LASTEXITCODE -ne 0) { throw 'aggregation failed' }
