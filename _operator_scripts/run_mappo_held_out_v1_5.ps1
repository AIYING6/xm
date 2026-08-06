# run_mappo_held_out_v1_5.ps1
# One-shot FORMAL HELD-OUT test (FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5).
# 27 locked checkpoints x 4 scenarios x 100 episodes = 10,800 episodes, serial.
#
# Evidence chain (frozen):
#   protocol   FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5
#   base seed  745669 (derived from joint manifest SHA, never used before)
#   split      test
#   updates    ONLY the per-(method,seed) locked updates from the split manifest
#   no selection / no reselection / no checkpoint replacement
#
# Each of the 27 calls evaluates exactly ONE locked (method, seed, update):
#   --split test --seeds <s> --checkpoint-updates <locked> --base-seed 745669
#   --episodes 100 --scenarios 4 --eval-batch-size 1 --device cuda
# Output per method-seed subdir: held_out_v1.5/<method>/seed<s>/
# (selection CSV may be emitted by frozen code but is NOT used for decisions.)
$ErrorActionPreference = "Stop"

$Python = "D:\Anaconda\envs\.conda\envs\cac\python.exe"
$WorkRoot = "D:\Code\Codex\ri_gmappo_uav_mappo_v1.5"
$AbWorkRoot = "D:\Code\Codex\ri_gmappo_uav_ablation_v1.5"
$V14 = "D:\Code\Codex\ri_gmappo_uav\results\paper_config_runs\formal_budget_post_sixth_freeze_v1.4_formal_main_20260802"
$V15 = "$AbWorkRoot\results\paper_config_runs\formal_ablation_v1.5_ppo_977_20260804"
$MappoRoot = "$WorkRoot\results\paper_config_runs\formal_mappo_v1.5_ppo_977_20260806"
$OutRoot = "$WorkRoot\results\paper_config_runs\formal_held_out_v1_5_10800_20260807"
$SplitManifest = "$WorkRoot\docs\held_out_v1_5_assets\held_out_split_manifest.csv"
$Sweep = "$AbWorkRoot\scripts\evaluate_3d_checkpoint_sweep.py"
$HappoSweep = "$AbWorkRoot\scripts\evaluate_happo_checkpoint_sweep.py"
$MappoSweep = "$WorkRoot\scripts\evaluate_mappo_v1_5.py"
$LogDir = "$OutRoot\_operator_notes\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$TS = Get-Date -Format "yyyyMMdd_HHmmss"
$Summary = "$LogDir\held_out_summary_$TS.txt"
Add-Content $Summary "HELD-OUT start: $TS (split=test base_seed=745669 episodes=100 protocol=FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5)"

$Common = @(
    "--split", "test", "--base-seed", "745669", "--episodes", "100",
    "--eval-batch-size", "1",
    "--scenarios", "dropout030_delay2_relay_failure_early", "dropout030_delay2_relay_failure",
    "dropout030_delay2_relay_failure_delayed", "dropout030_delay2_relay_failure_late",
    "--target-policy", "straight", "--strict-target-sensing", "--agent-target-info-bottleneck",
    "--target-prior-position", "10000", "0", "5000",
    "--max-target-message-age-steps", "80", "--min-target-confidence", "0.2",
    "--selection-metric", "legacy_recovery", "--selection-success-weight", "100",
    "--max-selection-collision-rate", "0.0", "--selection-policy", "v1_5_wilson",
    "--selection-group", "suite", "--device", "cuda"
)

function Get-LockedUpdate([string]$method, [string]$seed) {
    $row = Import-Csv $SplitManifest | Where-Object { $_.method -eq $method -and $_.train_seed -eq $seed } | Select-Object -First 1
    if (-not $row) { throw "split manifest: no row for $method seed$seed" }
    return $row.selected_checkpoint_update
}

function Invoke-ShaGuard([string]$method, [string]$seed, [string]$ckptAbs) {
    $row = Import-Csv $SplitManifest | Where-Object { $_.method -eq $method -and $_.train_seed -eq $seed } | Select-Object -First 1
    $expected = $row.manifest_sha256
    $actual = (Get-FileHash -Algorithm SHA256 -Path $ckptAbs).Hash
    if ($actual -ne $expected) {
        throw "SHA MISMATCH $method seed${seed}: file=$actual manifest=$expected"
    }
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] SHA ok $method seed${seed} $expected"
}

function Invoke-Task([string]$method, [int]$seed, [string]$ckptAbs, [string]$script, [string[]]$extra) {
    $outDir = "$OutRoot\held_out_v1.5\$method\seed$seed"
    if (Test-Path "$outDir\COMPLETE") { Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] SKIP $method/seed$seed (COMPLETE)"; return }
    if (Test-Path "$outDir\IN_PROGRESS") { throw "IN_PROGRESS exists: $method/seed$seed" }
    $locked = Get-LockedUpdate $method "$seed"
    Invoke-ShaGuard $method "$seed" $ckptAbs
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    Add-Content "$outDir\IN_PROGRESS" "start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] start $method/seed$seed locked=$locked"
    $log = "$LogDir\${method}_seed${seed}_$TS.log"
    $full = $Common + @("--seeds", "$seed", "--checkpoint-updates", "$locked") + $extra + @("--out-dir", $outDir)
    & $Python -B $script @full *> $log
    $code = $LASTEXITCODE
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] done $method/seed$seed exit=$code log=$log"
    if ($code -ne 0) { throw "HELD-OUT FAILED $method/seed$seed exit=$code log=$log" }
    Remove-Item "$outDir\IN_PROGRESS" -ErrorAction SilentlyContinue
    Add-Content "$outDir\COMPLETE" "done $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=0"
}

# ---- method configs (frozen mapping; mirrors validation run) ----
$Cfg = @{
    "full_ea_rg"           = @{ root = "$V14\ea_rg_mappo_s_gate_prior"; enc = "multi_relation"; rel = "none"; msg = "none"; prior = "0.4"; fixed = "0.5" }
    "w_o_gate_prior"       = @{ root = "$V15\w_o_gate_prior"; enc = "multi_relation"; rel = "none"; msg = "none"; prior = "0.0"; fixed = "0.5" }
    "w_o_task_support"     = @{ root = "$V15\w_o_task_support"; enc = "multi_relation"; rel = "no_task_support"; msg = "none"; prior = "0.4"; fixed = "0.5" }
    "w_o_role_pair_gate"   = @{ root = "$V15\w_o_role_pair_gate"; enc = "multi_relation"; rel = "none"; msg = "no_role_pair_gate"; prior = "0.4"; fixed = "0.598687660112452" }
    "no_graph"             = @{ root = "$V14\no_graph"; enc = "no_graph"; rel = "none"; msg = "none"; prior = "0.0"; fixed = "0.5" }
    "single_graph"         = @{ root = "$V14\single_graph"; enc = "single"; rel = "none"; msg = "none"; prior = "0.0"; fixed = "0.5" }
    "param_matched_single" = @{ root = "$V14\param_matched_single"; enc = "single"; rel = "none"; msg = "none"; prior = "0.0"; fixed = "0.5" }
}

foreach ($method in @("full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate", "no_graph", "single_graph", "param_matched_single")) {
    $c = $Cfg[$method]
    $encArg = if ($c.enc -eq "multi_relation") { "--multi-root" } elseif ($c.enc -eq "no_graph") { "--no-graph-root" } else { "--single-root" }
    foreach ($seed in 0, 1, 2) {
        $upd4 = ([int](Get-LockedUpdate $method "$seed")).ToString("D4")
        $ckpt = "$($c.root)\ppo_seed${seed}_1m\actor_critic_update_${upd4}.pt"
        $extra = @(
            "--graph-encoders", $c.enc, $encArg, $c.root,
            "--run-dir-template", "ppo_seed{seed}_1m",
            "--checkpoint-glob", "actor_critic_update_*.pt",
            "--graph-relation-ablation", $c.rel, "--graph-message-ablation", $c.msg,
            "--role-gate-prior-strength", $c.prior, "--role-pair-gate-fixed-value", $c.fixed
        )
        Invoke-Task $method $seed $ckpt $Sweep $extra
    }
}

# happo (v1.4, separate entrypoint)
foreach ($seed in 0, 1, 2) {
    $locked = Get-LockedUpdate "happo" "$seed"
    $upd4 = ([int]$locked).ToString("D4")
    $ckpt = "$V14\happo\ppo_seed${seed}_1m\happo_update_${upd4}.pt"
    $extra = @("--happo-root", "$V14\happo", "--run-dir-template", "ppo_seed{seed}_1m", "--checkpoint-glob", "happo_update_*.pt")
    Invoke-Task "happo" $seed $ckpt $HappoSweep $extra
}

# mappo (MAPPO worktree, separate entrypoint, run-dir has no _1m suffix)
foreach ($seed in 0, 1, 2) {
    $locked = Get-LockedUpdate "mappo" "$seed"
    $upd4 = ([int]$locked).ToString("D4")
    $ckpt = "$MappoRoot\ppo_seed${seed}\actor_critic_update_${upd4}.pt"
    $extra = @("--mappo-root", $MappoRoot, "--run-dir-template", "ppo_seed{seed}", "--checkpoint-glob", "actor_critic_update_*.pt")
    Invoke-Task "mappo" $seed $ckpt $MappoSweep $extra
}

Add-Content $Summary "ALL 27 HELD-OUT TASKS DONE: $TS"
Write-Output "all 27 held-out tasks complete (10,800 episodes)"
