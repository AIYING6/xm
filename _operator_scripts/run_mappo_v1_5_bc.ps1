# run_mappo_v1_5_bc.ps1
# MAPPO formal BC generation (3 seeds, serial, CPU) at frozen code
# mappo-freeze-v1.5.0 @ 11fa019. Output root is brand-new (no _smoke reuse).
#
# Frozen formal parameters:
#   seeds 0,1,2 | episodes 120 | epochs 20 | batch-size 256 | hidden-dim 64
#   device cpu | serial | pretrained_modules=actor | role_dim=4 (derived)
#   critic random init (NOT in BC) | code/tag mappo-freeze-v1.5.0 @ 11fa019
#   env params identical to the v1.5 Full frozen config (no manual re-typing).
$ErrorActionPreference = "Stop"

$Python = "D:\Anaconda\envs\.conda\envs\cac\python.exe"
$WorkRoot = "D:\Code\Codex\ri_gmappo_uav_mappo_v1.5"
$OutRoot = "$WorkRoot\results\paper_config_runs\formal_mappo_v1.5_bc_freeze_20260806"
$BcScript = "$WorkRoot\scripts\pretrain_mappo_3d_bc.py"
$Verify = "$WorkRoot\_operator_scripts\verify_mappo_bc_seed.py"
$LogDir = "$OutRoot\_bc_operator_notes\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$TS = Get-Date -Format "yyyyMMdd_HHmmss"
$Summary = "$LogDir\mappo_bc_summary_$TS.txt"
Add-Content $Summary "MAPPO BC run start: $TS (freeze mappo-freeze-v1.5.0 @ 11fa019)"

$Common = @(
    "--episodes", "120", "--epochs", "20", "--batch-size", "256",
    "--hidden-dim", "64", "--device", "cpu",
    "--target-policy", "straight", "--strict-target-sensing",
    "--agent-target-info-bottleneck",
    "--target-prior-position", "10000", "0", "5000",
    "--max-target-message-age-steps", "80", "--min-target-confidence", "0.2",
    "--communication-dropout-prob", "0.30", "--message-delay-steps", "2",
    "--failed-blue-agent", "1",
    "--node-failure-start-random-min", "25", "--node-failure-start-random-max", "70",
    "--node-failure-duration-steps", "80", "--attack-hold-steps", "4",
    "--min-success-step", "80",
    "--code-commit", "mappo-freeze-v1.5.0 @ 11fa019"
)

function Invoke-BCTask([int]$seed) {
    $outDir = Join-Path $OutRoot "bc_seed$seed"
    if (Test-Path (Join-Path $outDir "COMPLETE")) {
        Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] SKIP bc_seed$seed (COMPLETE exists)"
        return
    }
    if (Test-Path (Join-Path $outDir "IN_PROGRESS")) {
        throw "IN_PROGRESS marker exists for bc_seed$seed; refusing to continue (possible prior partial run)."
    }
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    Add-Content (Join-Path $outDir "IN_PROGRESS") "start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $log = Join-Path $LogDir "bc_seed${seed}_$TS.log"
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] start bc_seed$seed"
    & $Python -B $BcScript `
        --seed "$seed" `
        --out-dir $outDir `
        @Common *> $log
    $code = $LASTEXITCODE
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] BC done bc_seed$seed exit=$code log=$log"
    if ($code -ne 0) { throw "BC FAILED: bc_seed$seed exit=$code log=$log" }
    # per-seed acceptance check (immediate)
    & $Python -B $Verify --root $OutRoot --seed "$seed" *>> $log
    $vcode = $LASTEXITCODE
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] verify bc_seed$seed exit=$vcode log=$log"
    if ($vcode -ne 0) { throw "VERIFY FAILED: bc_seed$seed exit=$vcode log=$log" }
    Remove-Item (Join-Path $outDir "IN_PROGRESS") -ErrorAction SilentlyContinue
    Add-Content (Join-Path $outDir "COMPLETE") "done $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=0 verify=PASS"
}

Invoke-BCTask 0
Invoke-BCTask 1
Invoke-BCTask 2

Add-Content $Summary "ALL 3 MAPPO BC DONE: $TS"
Write-Output "all 3 MAPPO formal BC complete"
