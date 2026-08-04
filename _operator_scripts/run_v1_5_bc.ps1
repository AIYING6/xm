$ErrorActionPreference = "Stop"

# ============================================================
# v1.5 formal BC generation (9 tasks, serial).
# freeze commit a048e91 / tag formal-ablation-freeze-v1.5.1
# ============================================================

$Python = "D:\Anaconda\envs\.conda\envs\cac\python.exe"
$WorkRoot = "D:\Code\Codex\ri_gmappo_uav_ablation_v1.5"
$OutRoot = "D:\Code\Codex\ri_gmappo_uav_ablation_v1.5\results\paper_config_runs\formal_ablation_v1.5_bc_freeze_20260804"
$BcScript = Join-Path $WorkRoot "scripts\pretrain_ri_gmappo_3d_bc.py"
$LogDir = Join-Path $OutRoot "_bc_operator_notes\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$TimeStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Summary = Join-Path $LogDir "bc_summary_$TimeStamp.txt"
Add-Content -Path $Summary -Value "v1.5 BC run start: $TimeStamp (freeze a048e91 / formal-ablation-freeze-v1.5.1)"

$Common = @(
    "--episodes", "120", "--epochs", "20", "--batch-size", "256",
    "--hidden-dim", "64", "--role-dim", "8", "--intent-dim", "8",
    "--graph-encoder", "multi_relation",
    "--graph-input-ablation", "none",
    "--geometric-policy-mode", "offset", "--attacker-action-weight", "2.0",
    "--target-policy", "straight", "--strict-target-sensing",
    "--agent-target-info-bottleneck",
    "--communication-dropout-prob", "0.30", "--message-delay-steps", "2",
    "--failed-blue-agent", "1",
    "--node-failure-start-random-min", "25", "--node-failure-start-random-max", "70",
    "--node-failure-duration-steps", "80", "--attack-hold-steps", "4",
    "--min-success-step", "80",
    "--device", "cpu"
)

function Invoke-BCTask([string]$ablation, [int]$seed, [string]$relAbl, [string]$msgAbl, [string]$gatePrior, [string]$fixedGate) {
    $outDir = Join-Path $OutRoot "$ablation\bc_seed$seed"
    if (Test-Path (Join-Path $outDir "COMPLETE")) {
        Add-Content -Path $Summary -Value "[$(Get-Date -Format 'HH:mm:ss')] SKIP $ablation seed$seed (COMPLETE exists)"
        return
    }
    if (Test-Path (Join-Path $outDir "IN_PROGRESS")) {
        throw "IN_PROGRESS marker exists for $ablation seed$seed; refusing to continue (possible prior partial run)."
    }
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    Add-Content -Path (Join-Path $outDir "IN_PROGRESS") -Value "start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $log = Join-Path $LogDir "${ablation}_seed${seed}_$TimeStamp.log"
    Add-Content -Path $Summary -Value "[$(Get-Date -Format 'HH:mm:ss')] start $ablation seed$seed"
    & $Python -B $BcScript `
        --graph-relation-ablation $relAbl `
        --graph-message-ablation $msgAbl `
        --role-gate-prior-strength $gatePrior `
        --role-pair-gate-fixed-value $fixedGate `
        --seed "$seed" `
        --out-dir $outDir `
        @Common *> $log
    $code = $LASTEXITCODE
    Add-Content -Path $Summary -Value "[$(Get-Date -Format 'HH:mm:ss')] done $ablation seed$seed exit=$code log=$log"
    if ($code -ne 0) {
        throw "BC FAILED: $ablation seed$seed exit=$code log=$log"
    }
    Remove-Item (Join-Path $outDir "IN_PROGRESS") -ErrorAction SilentlyContinue
    Add-Content -Path (Join-Path $outDir "COMPLETE") -Value "done $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=0"
}

# w_o_gate_prior
Invoke-BCTask "w_o_gate_prior" 0 "none" "none" "0.0" "0.5"
Invoke-BCTask "w_o_gate_prior" 1 "none" "none" "0.0" "0.5"
Invoke-BCTask "w_o_gate_prior" 2 "none" "none" "0.0" "0.5"
# w_o_task_support
Invoke-BCTask "w_o_task_support" 0 "no_task_support" "none" "0.4" "0.5"
Invoke-BCTask "w_o_task_support" 1 "no_task_support" "none" "0.4" "0.5"
Invoke-BCTask "w_o_task_support" 2 "no_task_support" "none" "0.4" "0.5"
# w_o_role_pair_gate
Invoke-BCTask "w_o_role_pair_gate" 0 "none" "no_role_pair_gate" "0.4" "0.598687660112452"
Invoke-BCTask "w_o_role_pair_gate" 1 "none" "no_role_pair_gate" "0.4" "0.598687660112452"
Invoke-BCTask "w_o_role_pair_gate" 2 "none" "no_role_pair_gate" "0.4" "0.598687660112452"

Add-Content -Path $Summary -Value "ALL 9 BC DONE: $TimeStamp"
Write-Output "all 9 v1.5 BC complete"
