# run_mappo_v1_5_ppo.ps1
# MAPPO formal PPO (3 seeds, serial on GPU) at frozen code
# mappo-freeze-v1.5.0 @ 11fa019 (training entry: scripts/train_mappo_3d_formal_v1_5.py).
#
# Frozen formal parameters:
#   seeds 0,1,2 | num_envs 8 | rollout_steps 128 | updates 977
#   = 8 x 128 x 977 = 1,000,448 env steps (identical budget to v1.5 Full)
#   init-checkpoint = formal BC bc_seed{seed}/mappo_bc_actor.pt
#   device cuda | save_interval 100 | save_snapshots
#   env params identical to the v1.5 Full frozen config (programmatic defaults).
$ErrorActionPreference = "Stop"

$Python = "D:\Anaconda\envs\.conda\envs\cac\python.exe"
$WorkRoot = "D:\Code\Codex\ri_gmappo_uav_mappo_v1.5"
$BcRoot = "$WorkRoot\results\paper_config_runs\formal_mappo_v1.5_bc_freeze_20260806"
$OutRoot = "$WorkRoot\results\paper_config_runs\formal_mappo_v1.5_ppo_977_20260806"
$TrainScript = "$WorkRoot\scripts\train_mappo_3d_formal_v1_5.py"
$LogDir = "$OutRoot\_operator_notes\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$TS = Get-Date -Format "yyyyMMdd_HHmmss"
$Summary = "$LogDir\mappo_ppo_summary_$TS.txt"
Add-Content $Summary "MAPPO PPO run start: $TS (freeze mappo-freeze-v1.5.0 @ 11fa019, budget 8x128x977)"

$Common = @(
    "--num-envs", "8", "--rollout-steps", "128", "--updates", "977",
    "--hidden-dim", "64", "--device", "cuda",
    "--target-policy", "straight", "--strict-target-sensing",
    "--agent-target-info-bottleneck",
    "--target-prior-position", "10000", "0", "5000",
    "--max-target-message-age-steps", "80", "--min-target-confidence", "0.2",
    "--communication-dropout-prob", "0.30", "--message-delay-steps", "2",
    "--failed-blue-agent", "1",
    "--node-failure-start-random-min", "25", "--node-failure-start-random-max", "70",
    "--node-failure-duration-steps", "80", "--attack-hold-steps", "4",
    "--min-success-step", "80",
    "--save-interval", "100", "--save-snapshots",
    "--code-commit", "mappo-freeze-v1.5.0 @ 11fa019"
)

function Invoke-PpoTask([int]$seed) {
    $outDir = Join-Path $OutRoot "ppo_seed$seed"
    $bcCkpt = Join-Path $BcRoot "bc_seed$seed\mappo_bc_actor.pt"
    if (-not (Test-Path $bcCkpt)) { throw "BC checkpoint missing: $bcCkpt" }
    if (Test-Path (Join-Path $outDir "COMPLETE")) {
        Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] SKIP ppo_seed$seed (COMPLETE exists)"
        return
    }
    if (Test-Path (Join-Path $outDir "IN_PROGRESS")) {
        throw "IN_PROGRESS marker exists for ppo_seed$seed; refusing to continue (possible prior partial run)."
    }
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    Add-Content (Join-Path $outDir "IN_PROGRESS") "start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $log = Join-Path $LogDir "ppo_seed${seed}_$TS.log"
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] start ppo_seed$seed bc=$bcCkpt"
    & $Python -B $TrainScript `
        --seed "$seed" `
        --init-checkpoint $bcCkpt `
        --out-dir $outDir `
        @Common *> $log
    $code = $LASTEXITCODE
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] done ppo_seed$seed exit=$code log=$log"
    if ($code -ne 0) { throw "PPO FAILED: ppo_seed$seed exit=$code log=$log" }
    Remove-Item (Join-Path $outDir "IN_PROGRESS") -ErrorAction SilentlyContinue
    Add-Content (Join-Path $outDir "COMPLETE") "done $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=0"
}

Invoke-PpoTask 0
Invoke-PpoTask 1
Invoke-PpoTask 2

Add-Content $Summary "ALL 3 MAPPO PPO DONE: $TS"
Write-Output "all 3 MAPPO formal PPO complete"
