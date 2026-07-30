param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("no_graph", "single_graph", "param_matched_single", "ea_rg_mappo_s_gate_prior", "happo")]
    [string]$Method,

    [Parameter(Mandatory = $true)]
    [ValidateSet(0, 1, 2)]
    [int]$Seed,

    [string]$Python = "python",
    [string]$Device = "cpu",
    [int]$TotalUpdates = 977,
    [int]$ChunkUpdates = 100,
    [string]$ExpectedTag = "formal-post-sixth-freeze-v1.1",
    # Escape hatch for development smoke runs. Outputs are NOT formal evidence.
    [switch]$AllowUnfrozen
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot/formal_freeze_gate.ps1"

# Formal protocol: terminate when HEAD != freeze commit or tracked source is dirty.
$FreezeCommit = Assert-FrozenWorkspace -ExpectedTag $ExpectedTag -AllowUnfrozen:$AllowUnfrozen

$Root = "results/paper_config_runs/formal_budget_post_sixth_freeze_v1"
$OutDir = "$Root/$Method/ppo_seed${Seed}_1m"
$LogPath = "$OutDir/train_log.csv"

# Authoritative resume source: training-state checkpoint (carries optimizer/RNG state).
# train_log.csv is audit-only and MUST NOT decide the resume start by itself.
function Get-LogStats {
    param([string]$Path)
    $stats = @{ MaxUpdate = 0; Count = 0; Duplicate = 0; OutOfOrder = 0 }
    if (-not (Test-Path $Path)) {
        return $stats
    }
    $rows = @(Import-Csv $Path)
    $stats.Count = $rows.Count
    if ($rows.Count -eq 0) {
        return $stats
    }
    $updates = @()
    foreach ($row in $rows) {
        if ($row.update -match "^\d+$") {
            $updates += [int]$row.update
        }
    }
    if ($updates.Count -eq 0) {
        return $stats
    }
    $stats.MaxUpdate = ($updates | Measure-Object -Maximum).Maximum
    $stats.Duplicate = $updates.Count - ($updates | Sort-Object -Unique).Count
    $ooo = 0
    for ($i = 1; $i -lt $updates.Count; $i++) {
        if ($updates[$i] -lt $updates[$i - 1]) { $ooo++ }
    }
    $stats.OutOfOrder = $ooo
    return $stats
}

# Returns a hashtable: Update, OptimizerExists, Loadable.
function Get-CheckpointInfo {
    param([string]$Python, [string]$StatePath)
    $info = @{ Update = 0; OptimizerExists = $false; Loadable = $false }
    if (-not (Test-Path $StatePath)) {
        return $info
    }
    $code = @'
import sys, torch
p = sys.argv[1]
try:
    payload = torch.load(p, map_location="cpu", weights_only=False)
    update = int(payload.get("update", 0))
    opt = bool(payload.get("optimizer_state") or payload.get("optimizer_states"))
    print(f"{update} {int(opt)} 1")
except Exception as e:
    print(f"0 0 0")
'@
    $out = & $Python -c $code $StatePath 2>$null
    if ($out -match "^(?<u>-?\d+) (?<o>[01]) (?<l>[01])$") {
        $info.Update = [int]$Matches.u
        $info.OptimizerExists = ($Matches.o -eq "1")
        $info.Loadable = ($Matches.l -eq "1")
    }
    return $info
}

$StatePath = if ($Method -eq "happo") {
    "$OutDir/happo_training_state_latest.pt"
} else {
    "$OutDir/actor_critic_training_state_latest.pt"
}

$LogStats = Get-LogStats $LogPath
$Ckpt = Get-CheckpointInfo $Python $StatePath

$InitCheckpoint = if ($Method -eq "happo") {
    "$Root/happo/bc_seed$Seed/happo_bc_latest.pt"
} else {
    "$Root/$Method/bc_seed$Seed/actor_critic_latest.pt"
}

$LogMaxUpdate = $LogStats.MaxUpdate

$HasTrainingState = Test-Path $StatePath
$HasLog = Test-Path $LogPath
$SnapPattern = if ($Method -eq "happo") { "happo_update_*.pt" } else { "actor_critic_update_*.pt" }
$HasSnapshot = @(Get-ChildItem -Path $OutDir -Filter $SnapPattern -ErrorAction SilentlyContinue).Count -gt 0
$HasBC = Test-Path $InitCheckpoint

# FRESH start requires: no training state, no log, no snapshot, but a valid BC init.
$IsFreshStart = (-not $HasTrainingState) -and (-not $HasLog) -and (-not $HasSnapshot)

# PARTIAL_FRESH_STATE: no training state, but partial artifacts already exist.
# Must NOT auto-overwrite from BC; block for manual inspection.
if (-not $HasTrainingState -and ($HasLog -or $HasSnapshot)) {
    Write-Error "BLOCKED (PARTIAL_FRESH_STATE): no training state but partial artifacts present (log=$HasLog, snapshot=$HasSnapshot). Inspect manually; do not auto-restart from BC."
    exit 2
}

Write-Host "Formal 1M chunk pre-flight: method=$Method seed=$Seed ckpt_update=$($Ckpt.Update) log_max=$LogMaxUpdate fresh=$IsFreshStart bc=$HasBC target=$TotalUpdates"

if ($IsFreshStart) {
    # Fresh start from BC init: no resume, no log consistency required.
    if (-not (Test-Path $InitCheckpoint)) {
        Write-Error "BLOCKED: fresh start requires BC init checkpoint: $InitCheckpoint"
        exit 2
    }
    # Existence is not enough: the BC init must load on CPU, carry a non-empty
    # state dict, match this method's architecture exactly, and be stamped with
    # the freeze commit. Otherwise a truncated/empty/wrong-method checkpoint
    # would silently seed a "formal" run.
    & $Python "scripts/verify_bc_checkpoint.py" --root $Root --method $Method --seed $Seed --expected-commit $FreezeCommit
    if ($LASTEXITCODE -ne 0) {
        Write-Error "BLOCKED: BC init failed verification (method=$Method seed=$Seed)."
        exit 2
    }
    $ResumeStartUpdate = 0
    $LastUpdate = 0
    $RunUpdates = [Math]::Min($ChunkUpdates, $TotalUpdates)
    $Resume = $false
    Write-Host "Formal 1M chunk (FRESH from BC): method=$Method seed=$Seed run=$RunUpdates target=$TotalUpdates"
} else {
    # Authoritative resume update is the training-state checkpoint update.
    $ResumeStartUpdate = $Ckpt.Update

    # Hard pre-flight gate: do NOT guess or continue if any condition fails.
    if (-not $Ckpt.Loadable) {
        Write-Error "BLOCKED: training-state checkpoint not loadable: $StatePath"
        exit 2
    }
    if (-not $Ckpt.OptimizerExists) {
        Write-Error "BLOCKED: training-state checkpoint missing optimizer state; strict resume impossible."
        exit 2
    }
    if ($LogStats.Duplicate -ne 0) {
        Write-Error "BLOCKED: train_log.csv has $($LogStats.Duplicate) duplicate update(s); repair before resume."
        exit 2
    }
    if ($LogStats.OutOfOrder -ne 0) {
        Write-Error "BLOCKED: train_log.csv has $($LogStats.OutOfOrder) out-of-order update(s); repair before resume."
        exit 2
    }
    if ($LogMaxUpdate -ne $Ckpt.Update) {
        Write-Error "BLOCKED: log_max_update=$LogMaxUpdate != training_checkpoint_update=$($Ckpt.Update); resolve inconsistency before resume."
        exit 2
    }
    if ($ResumeStartUpdate -ge $TotalUpdates) {
        Write-Host "Already complete: method=$Method seed=$Seed update=$ResumeStartUpdate/$TotalUpdates"
        exit 0
    }
    $LastUpdate = $ResumeStartUpdate
    $RunUpdates = [Math]::Min($ChunkUpdates, $TotalUpdates - $ResumeStartUpdate)
    $Resume = $Ckpt.Update -gt 0
    Write-Host "Formal 1M chunk: method=$Method seed=$Seed resume_start=$ResumeStartUpdate run=$RunUpdates target=$TotalUpdates"
}

function Common-RiArgs {
    param(
        [string]$Graph,
        [int]$Hidden,
        [string]$GatePrior
    )
    $args = @(
        "scripts/train_ri_gmappo.py",
        "--env-name", "3d_intercept",
        "--seed", "$Seed", "--num-envs", "8", "--rollout-steps", "128", "--updates", "$RunUpdates",
        "--hidden-dim", "$Hidden", "--role-dim", "8", "--intent-dim", "8",
        "--graph-encoder", $Graph,
        "--role-gate-prior-strength", $GatePrior,
        "--actor-lr", "5e-5", "--critic-lr", "1e-4",
        "--clip-coef", "0.1", "--ppo-epochs", "2", "--target-kl", "0.01",
        "--entropy-coef", "0.003", "--max-grad-norm", "0.5", "--critic-warmup-updates", "20",
        "--eval-interval", "100", "--eval-episodes", "5", "--eval-base-seed", "391000",
        "--save-interval", "100", "--save-snapshots",
        "--target-policy", "straight",
        "--strict-target-sensing", "--agent-target-info-bottleneck",
        "--communication-dropout-prob", "0.30", "--message-delay-steps", "2",
        "--failed-blue-agent", "1",
        "--node-failure-start-random-min", "25", "--node-failure-start-random-max", "70",
        "--node-failure-duration-steps", "80", "--attack-hold-steps", "4", "--min-success-step", "80",
        "--post-loss-chain-reclosure-reward-weight", "0.5",
        "--post-loss-chain-reclosure-min-step", "80",
        "--safety-proximity-distance", "2500",
        "--safety-proximity-penalty-weight", "0.5",
        "--device", $Device,
        "--out-dir", $OutDir
    )
    if ($Resume) {
        $args += @(
            "--resume", "$OutDir/actor_critic_training_state_latest.pt",
            "--update-offset", "$LastUpdate",
            "--append-log"
        )
    } else {
        $args += @(
            "--init-checkpoint", "$Root/$Method/bc_seed$Seed/actor_critic_latest.pt"
        )
    }
    return $args
}

function HappoArgs {
    $args = @(
        "scripts/train_happo_baseline.py",
        "--seed", "$Seed", "--num-envs", "8", "--rollout-steps", "128", "--updates", "$RunUpdates",
        "--hidden-dim", "64", "--role-dim", "8", "--intent-dim", "8",
        "--lr", "5e-5", "--clip-coef", "0.1", "--ppo-epochs", "2",
        "--entropy-coef", "0.003", "--max-grad-norm", "0.5",
        "--eval-interval", "100", "--eval-episodes", "5", "--eval-base-seed", "391000",
        "--save-interval", "100", "--save-snapshots",
        "--target-policy", "straight",
        "--strict-target-sensing", "--agent-target-info-bottleneck",
        "--communication-dropout-prob", "0.30", "--message-delay-steps", "2",
        "--failed-blue-agent", "1",
        "--node-failure-start-random-min", "25", "--node-failure-start-random-max", "70",
        "--node-failure-duration-steps", "80", "--attack-hold-steps", "4", "--min-success-step", "80",
        "--safety-proximity-distance", "2500",
        "--safety-proximity-penalty-weight", "0.5",
        "--device", $Device,
        "--out-dir", $OutDir
    )
    if ($Resume) {
        $args += @(
            "--resume", "$OutDir/happo_training_state_latest.pt",
            "--update-offset", "$LastUpdate",
            "--append-log"
        )
    } else {
        $args += @(
            "--init-checkpoint", "$Root/happo/bc_seed$Seed/happo_bc_latest.pt"
        )
    }
    return $args
}

switch ($Method) {
    "no_graph" {
        $Args = Common-RiArgs -Graph "no_graph" -Hidden 64 -GatePrior "0.0"
    }
    "single_graph" {
        $Args = Common-RiArgs -Graph "single" -Hidden 64 -GatePrior "0.0"
    }
    "param_matched_single" {
        $Args = Common-RiArgs -Graph "single" -Hidden 96 -GatePrior "0.0"
    }
    "ea_rg_mappo_s_gate_prior" {
        $Args = Common-RiArgs -Graph "multi_relation" -Hidden 64 -GatePrior "0.4"
    }
    "happo" {
        $Args = HappoArgs
    }
}

& $Python @Args
