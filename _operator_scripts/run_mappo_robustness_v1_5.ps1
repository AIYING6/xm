# run_mappo_robustness_v1_5.ps1
# Formal robustness run (FORMAL_ROBUSTNESS_PROTOCOL_V1_5, ops
# robustness-eval-ops-v1.5.0 @ f808f9a).
# 7 methods x 3 seeds x 10 conditions (R00-R09) x 50 episodes = 10,500.
# Serial, single Scheduled Task. No selection; locked checkpoints only.
#
# Per-call guards (BEFORE): method, train_seed, locked_update, checkpoint_path,
# checkpoint_sha256, condition_id, condition 5 params, base_seed=946804,
# episodes=50, split=test.
# Per-call checks (AFTER): exit=0, episode=50, summary=1, selection=0,
# COMPLETE present, IN_PROGRESS absent, no Traceback, no illegal NaN/Inf.
# Any failure stops the whole orchestrator (no skip, no partial continue).
$ErrorActionPreference = "Stop"

$Python = "D:\Anaconda\envs\.conda\envs\cac\python.exe"
$WorkRoot = "D:\Code\Codex\ri_gmappo_uav_mappo_v1.5"
$AbRoot = "D:\Code\Codex\ri_gmappo_uav_ablation_v1.5"
$V14 = "D:\Code\Codex\ri_gmappo_uav\results\paper_config_runs\formal_budget_post_sixth_freeze_v1.4_formal_main_20260802"
$V15 = "$AbRoot\results\paper_config_runs\formal_ablation_v1.5_ppo_977_20260804"
$MappoRoot = "$WorkRoot\results\paper_config_runs\formal_mappo_v1.5_ppo_977_20260806"
$OutRoot = "$WorkRoot\results\paper_config_runs\formal_robustness_v1.5_10500_20260807"
$Manifest = "$WorkRoot\docs\robustness_v1_5_assets\robustness_checkpoint_manifest.csv"
$SplitManifest = "$WorkRoot\docs\robustness_v1_5_assets\robustness_split_manifest.json"
$EvalScript = "$WorkRoot\scripts\evaluate_robustness_v1_5.py"
$VerifyScript = "$WorkRoot\_operator_scripts\verify_robustness_group.py"
$LogDir = "$OutRoot\_operator_notes\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$TS = Get-Date -Format "yyyyMMdd_HHmmss"
$Summary = "$LogDir\robustness_summary_$TS.txt"
Add-Content $Summary "ROBUSTNESS start: $TS (base_seed 946804 split=test episodes=50 conditions=R00..R09)"

# frozen method -> entrypoint + run-dir config
$MethodCfg = @{
    "full_ea_rg"           = @{ entry = "sweep"; root = "$V14\ea_rg_mappo_s_gate_prior"; enc = "multi_relation"; rel = "none"; msg = "none"; prior = "0.4"; fixed = "0.5" }
    "w_o_role_pair_gate"   = @{ entry = "sweep"; root = "$V15\w_o_role_pair_gate"; enc = "multi_relation"; rel = "none"; msg = "no_role_pair_gate"; prior = "0.4"; fixed = "0.598687660112452" }
    "w_o_gate_prior"       = @{ entry = "sweep"; root = "$V15\w_o_gate_prior"; enc = "multi_relation"; rel = "none"; msg = "none"; prior = "0.0"; fixed = "0.5" }
    "w_o_task_support"     = @{ entry = "sweep"; root = "$V15\w_o_task_support"; enc = "multi_relation"; rel = "no_task_support"; msg = "none"; prior = "0.4"; fixed = "0.5" }
    "param_matched_single" = @{ entry = "sweep"; root = "$V14\param_matched_single"; enc = "single"; rel = "none"; msg = "none"; prior = "0.0"; fixed = "0.5" }
    "happo"                = @{ entry = "happo"; root = "$V14\happo"; enc = "single"; rel = "none"; msg = "none"; prior = "0.0"; fixed = "0.5" }
    "mappo"                = @{ entry = "mappo"; root = "$MappoRoot"; enc = "single"; rel = "none"; msg = "none"; prior = "0.0"; fixed = "0.5" }
}

# load conditions (id -> key) from split manifest
$split = Get-Content $SplitManifest -Encoding UTF8 | ConvertFrom-Json
$condList = @()
foreach ($c in $split.conditions) { $condList += @{ id = $c.id; key = $c.key } }
if ($condList.Count -ne 10) { throw "split manifest conditions != 10" }

# load 21 checkpoints
$ckpts = @{}
Import-Csv $Manifest | ForEach-Object {
    $ckpts["$($_.method)/$($_.train_seed)"] = $_ 
}

$Common = @(
    "--split", "test", "--base-seed", "946804", "--episodes", "50",
    "--eval-batch-size", "1",
    "--target-policy", "straight", "--strict-target-sensing",
    "--agent-target-info-bottleneck",
    "--target-prior-position", "10000", "0", "5000",
    "--max-target-message-age-steps", "80", "--min-target-confidence", "0.2",
    "--selection-metric", "legacy_recovery", "--selection-success-weight", "100",
    "--max-selection-collision-rate", "0.0",
    "--selection-policy", "v1_5_wilson", "--selection-group", "suite",
    "--device", "cuda"
)

function Get-LockedUpdate([string]$method, [string]$seed) {
    return $ckpts["$method/$seed"].selected_checkpoint_update
}
function Get-CkptSha([string]$method, [string]$seed) {
    return $ckpts["$method/$seed"].manifest_sha256
}
function Invoke-ShaGuard([string]$method, [string]$seed, [string]$ckptAbs) {
    $row = $ckpts["$method/$seed"]
    $expected = $row.manifest_sha256
    $actual = (Get-FileHash -Algorithm SHA256 -Path $ckptAbs).Hash
    if ($actual -ne $expected) { throw "SHA MISMATCH $method seed$seed file=$actual manifest=$expected" }
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] SHA ok $method seed$seed $expected"
}

function Invoke-Cell([string]$method, [int]$seed, [string]$condId, [string]$condKey) {
    $outDir = "$OutRoot\$method\seed$seed\$condId"
    if (Test-Path "$outDir\COMPLETE") { Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] SKIP $method/seed$seed/$condId"; return }
    if (Test-Path "$outDir\IN_PROGRESS") { throw "IN_PROGRESS exists $method/seed$seed/$condId" }
    $cfg = $MethodCfg[$method]
    $ckpt = $ckpts["$method/$seed"]
    $locked = $ckpt.selected_checkpoint_update
    $ckptAbs = $ckpt.checkpoint_abs
    Invoke-ShaGuard $method "$seed" $ckptAbs
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    Add-Content "$outDir\IN_PROGRESS" "start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] start $method/seed$seed/$condId locked=$locked key=$condKey"
    $log = "$LogDir\${method}_seed${seed}_${condId}_$TS.log"
    $extra = @("--entry", $cfg.entry, "--scenarios", $condKey, "--seeds", "$seed", "--checkpoint-updates", $locked)
    if ($cfg.entry -eq "sweep") {
        $extra += @("--graph-encoders", $cfg.enc)
        if ($cfg.enc -eq "multi_relation") { $extra += @("--multi-root", $cfg.root) }
        else { $extra += @("--single-root", $cfg.root) }
        $extra += @("--run-dir-template", "ppo_seed{seed}_1m", "--checkpoint-glob", "actor_critic_update_*.pt",
                    "--graph-relation-ablation", $cfg.rel, "--graph-message-ablation", $cfg.msg,
                    "--role-gate-prior-strength", $cfg.prior, "--role-pair-gate-fixed-value", $cfg.fixed)
    } elseif ($cfg.entry -eq "happo") {
        $extra += @("--happo-root", $cfg.root, "--run-dir-template", "ppo_seed{seed}_1m", "--checkpoint-glob", "happo_update_*.pt")
    } else {
        $extra += @("--mappo-root", $cfg.root, "--run-dir-template", "ppo_seed{seed}", "--checkpoint-glob", "actor_critic_update_*.pt")
    }
    $full = $Common + $extra + @("--out-dir", $outDir)
    & $Python -B $EvalScript @full *> $log
    $code = $LASTEXITCODE
    if ($code -ne 0) { throw "EVAL FAILED $method/seed$seed/$condId exit=$code log=$log" }
    & $Python -B $VerifyScript --group-dir $outDir --condition $condKey --log $log *>> $log
    $vcode = $LASTEXITCODE
    if ($vcode -ne 0) { throw "VERIFY FAILED $method/seed$seed/$condId exit=$vcode log=$log" }
    Remove-Item "$outDir\IN_PROGRESS" -ErrorAction SilentlyContinue
    Add-Content "$outDir\COMPLETE" "done $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=0"
    Add-Content $Summary "[$(Get-Date -Format 'HH:mm:ss')] done $method/seed$seed/$condId exit=0"
}

foreach ($method in @("full_ea_rg", "w_o_role_pair_gate", "w_o_gate_prior", "w_o_task_support",
                      "param_matched_single", "happo", "mappo")) {
    if (-not $MethodCfg.ContainsKey($method)) { throw "no config for $method" }
    foreach ($seed in 0, 1, 2) {
        foreach ($cond in $condList) {
            Invoke-Cell $method $seed $cond.id $cond.key
        }
    }
}

Add-Content $Summary "ALL 210 ROBUSTNESS CELLS DONE: $TS"
Write-Output "all 210 robustness cells complete (10,500 episodes)"
