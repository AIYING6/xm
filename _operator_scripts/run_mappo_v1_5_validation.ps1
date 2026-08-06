# run_mappo_v1_5_validation.ps1
# MAPPO formal 641939 validation (single new method; the original 8-method
# 24-checkpoint lock is NOT re-run). Serial on GPU via Scheduled Task.
#
# Evidence chain:
#   training lock   mappo-ppo-training-lock-v1.5.0 @ 989e338
#   PPO entry       mappo-ppo-freeze-v1.5.0 @ 3d5346d
#   eval impl       mappo-freeze-v1.5.0 @ 11fa019
#   candidate list  from the training-audit manifest (mappo_candidate_manifest_30.json)
#
# Frozen formal parameters:
#   method=mappo | train_seeds 0,1,2 | updates 100..977
#   scenarios early/relay/delayed/late | episodes 50 | base_seed 641939
#   selection_policy v1_5_wilson | device cuda | serial
# Total: 3 x 10 x 4 x 50 = 6000 episodes.
$ErrorActionPreference = "Stop"

$Python = "D:\Anaconda\envs\.conda\envs\cac\python.exe"
$WorkRoot = "D:\Code\Codex\ri_gmappo_uav_mappo_v1.5"
$PpoRoot = "$WorkRoot\results\paper_config_runs\formal_mappo_v1.5_ppo_977_20260806"
$OutRoot = "$WorkRoot\results\paper_config_runs\formal_mappo_v1.5_validation_selector_v1.5.1_20260806"
$EvalScript = "$WorkRoot\scripts\evaluate_mappo_v1_5.py"
$LogDir = "$OutRoot\_operator_notes\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$TS = Get-Date -Format "yyyyMMdd_HHmmss"
$Summary = "$LogDir\mappo_validation_summary_$TS.txt"
Add-Content $Summary "MAPPO validation start: $TS (base_seed 641939, v1_5_wilson, freeze chain 989e338/3d5346d/11fa019)"

$EvalArgs = @(
    "--split", "validation",
    "--seeds", "0", "1", "2",
    "--scenarios", "dropout030_delay2_relay_failure_early", "dropout030_delay2_relay_failure",
    "dropout030_delay2_relay_failure_delayed", "dropout030_delay2_relay_failure_late",
    "--episodes", "50", "--eval-batch-size", "1", "--base-seed", "641939",
    "--target-policy", "straight", "--strict-target-sensing", "--agent-target-info-bottleneck",
    "--target-prior-position", "10000", "0", "5000",
    "--max-target-message-age-steps", "80", "--min-target-confidence", "0.2",
    "--checkpoint-updates", "100", "200", "300", "400", "500", "600", "700", "800", "900", "977",
    "--selection-metric", "legacy_recovery", "--selection-success-weight", "100",
    "--max-selection-collision-rate", "0.0", "--selection-policy", "v1_5_wilson",
    "--selection-group", "suite", "--device", "cuda"
)

$outDir = $OutRoot
if (Test-Path (Join-Path $outDir "COMPLETE")) {
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] SKIP (COMPLETE exists)"
    exit 0
}
if (Test-Path (Join-Path $outDir "IN_PROGRESS")) {
    throw "IN_PROGRESS marker exists; refusing to continue (possible prior partial run)."
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Add-Content (Join-Path $outDir "IN_PROGRESS") "start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] start MAPPO validation"

$full = $EvalArgs + @(
    "--mappo-root", $PpoRoot,
    "--run-dir-template", "ppo_seed{seed}",
    "--checkpoint-glob", "actor_critic_update_*.pt",
    "--out-dir", $outDir
)
$log = Join-Path $LogDir "mappo_validation_$TS.log"
& $Python -B $EvalScript @full *> $log
$code = $LASTEXITCODE
Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] done MAPPO validation exit=$code log=$log"
if ($code -ne 0) { throw "MAPPO VALIDATION FAILED exit=$code log=$log" }
Remove-Item (Join-Path $outDir "IN_PROGRESS") -ErrorAction SilentlyContinue
Add-Content (Join-Path $outDir "COMPLETE") "done $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=0"
Write-Output "MAPPO 641939 validation complete"
