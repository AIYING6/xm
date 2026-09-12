param(
    [string]$Root = 'results/development/pscr_rc_m1_20260912',
    [string]$Python = 'D:/Anaconda/envs/.conda/envs/cac/python.exe',
    [switch]$WaitForTraining
)

$ErrorActionPreference = 'Stop'
$arms = 'full', 'phase_control', 'permuted_reliability'
$seeds = 99901, 99902, 99903

if ($WaitForTraining) {
    while ($true) {
        $missing = @()
        foreach ($arm in $arms) {
            foreach ($seed in $seeds) {
                $checkpoint = Join-Path $Root "$arm/seed$seed/endpoint.pt"
                if (-not (Test-Path $checkpoint)) { $missing += $checkpoint }
            }
        }
        if ($missing.Count -eq 0) { break }
        Start-Sleep -Seconds 15
    }
}

foreach ($arm in $arms) {
    foreach ($seed in $seeds) {
        $checkpoint = Join-Path $Root "$arm/seed$seed/endpoint.pt"
        if (-not (Test-Path $checkpoint)) { throw "missing trained checkpoint: $checkpoint" }
        $evaluation = Join-Path $Root "$arm/evaluation_seed$seed"
        if (-not (Test-Path (Join-Path $evaluation 'episode_metrics.csv'))) {
            & $Python scripts/run_pscr_rc_mappo.py evaluate --arm $arm --seed $seed --checkpoint $checkpoint --output-root $evaluation --execute
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        $audit = Join-Path $Root "$arm/action_audit_seed$seed"
        if (-not (Test-Path (Join-Path $audit 'action_fractions.csv'))) {
            & $Python scripts/audit_pscr_p4_baseline_actions.py --seed $seed --checkpoint $checkpoint --agent-kind rc --arm $arm --output-root $audit --execute
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
    }
}

$aggregate = Join-Path $Root 'diagnostics/m1_endpoint'
if (-not (Test-Path (Join-Path $aggregate 'PSCR_RC_M1_SUMMARY.csv'))) {
    & $Python scripts/aggregate_pscr_rc_m1.py --root $Root --seeds $seeds --output $aggregate
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
