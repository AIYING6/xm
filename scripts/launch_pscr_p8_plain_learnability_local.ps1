param(
    [int]$Updates = 256,
    [int]$ParallelEnvs = 8,
    [string]$OutputRoot = "results/development/pscr_p8_plain_learnability_20260913"
)

$ErrorActionPreference = 'Stop'
$python = 'D:/Anaconda/envs/.conda/envs/cac/python.exe'
$seeds = 97111, 97112, 97113
if (Test-Path $OutputRoot) { throw "Refusing to overwrite $OutputRoot" }
New-Item -ItemType Directory -Force -Path $OutputRoot, (Join-Path $OutputRoot 'logs') | Out-Null

foreach ($seed in $seeds) {
    $run = Join-Path $OutputRoot "runs/plain_mappo/seed$seed"
    Write-Host "[P8 learnability] training seed $seed"
    & $python scripts/run_pscr_p8_plain_baseline.py train --seed $seed --updates $Updates --parallel-envs $ParallelEnvs --output-root $run --execute 2>&1 |
        Tee-Object -FilePath (Join-Path $OutputRoot "logs/train_seed$seed.log")
    if ($LASTEXITCODE -ne 0) { throw "training failed for seed $seed" }
}

foreach ($seed in $seeds) {
    $run = Join-Path $OutputRoot "runs/plain_mappo/seed$seed"
    $eval = Join-Path $OutputRoot "evaluations/plain_mappo/seed$seed"
    Write-Host "[P8 learnability] evaluating seed $seed"
    & $python scripts/run_pscr_p8_plain_baseline.py evaluate --seed ($seed + 1000) --checkpoint (Join-Path $run 'endpoint.pt') --output-root $eval --execute 2>&1 |
        Tee-Object -FilePath (Join-Path $OutputRoot "logs/evaluate_seed$seed.log")
    if ($LASTEXITCODE -ne 0) { throw "evaluation failed for seed $seed" }
}
& $python scripts/aggregate_pscr_p8_plain_learnability.py --root (Join-Path $OutputRoot 'diagnostics') --execute
if ($LASTEXITCODE -ne 0) { throw 'aggregation failed' }
