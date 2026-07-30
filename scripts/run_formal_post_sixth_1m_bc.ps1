# Regenerate BC initializations for the new post-sixth-freeze v1 baseline.
# Must run AFTER the env P0 fix (zero/mask on target prior + union-graph attack-edge removal)
# and BEFORE any PPO training. Same demonstration protocol as the frozen BC rule:
#   teacher=geometric offset, episodes=120, epochs=20, batch=256, balanced loss, attacker weight=2.0.
param(
    [string]$Python = "python",
    [string]$Root = "results/paper_config_runs/formal_budget_post_sixth_freeze_v1",
    [ValidateSet("all", "no_graph", "single_graph", "param_matched_single", "ea_rg_mappo_s_gate_prior", "happo")]
    [string]$Method = "all",
    [ValidateSet(0, 1, 2, 99)]
    [int]$Seed = 99
)

$ErrorActionPreference = "Stop"

function Invoke-BC {
    param(
        [string]$Python,
        [string]$Script,
        [string]$Graph,
        [int]$Hidden,
        [string]$GatePrior,
        [string]$OutDir
    )
    & $Python $Script `
        --episodes 120 --epochs 20 --batch-size 256 `
        --hidden-dim $Hidden --role-dim 8 --intent-dim 8 `
        --graph-encoder $Graph `
        --role-gate-prior-strength $GatePrior `
        --geometric-policy-mode offset --attacker-action-weight 2.0 `
        --seed $Seed --target-policy straight `
        --strict-target-sensing --agent-target-info-bottleneck `
        --communication-dropout-prob 0.30 --message-delay-steps 2 `
        --failed-blue-agent 1 `
        --node-failure-start-random-min 25 --node-failure-start-random-max 70 `
        --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 `
        --device cpu `
        --out-dir $OutDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "BC failed for $OutDir (exit $LASTEXITCODE)"
        exit 1
    }
}

$seeds = if ($Seed -eq 99) { @(0, 1, 2) } else { @($Seed) }

$jobs = @(
    @{ Method = "no_graph"; Script = "scripts/pretrain_ri_gmappo_3d_bc.py"; Graph = "no_graph"; Hidden = 64; GatePrior = "0.0" },
    @{ Method = "single_graph"; Script = "scripts/pretrain_ri_gmappo_3d_bc.py"; Graph = "single"; Hidden = 64; GatePrior = "0.0" },
    @{ Method = "param_matched_single"; Script = "scripts/pretrain_ri_gmappo_3d_bc.py"; Graph = "single"; Hidden = 96; GatePrior = "0.0" },
    @{ Method = "ea_rg_mappo_s_gate_prior"; Script = "scripts/pretrain_ri_gmappo_3d_bc.py"; Graph = "multi_relation"; Hidden = 64; GatePrior = "0.4" },
    @{ Method = "happo"; Script = "scripts/pretrain_happo_3d_bc.py"; Graph = "no_graph"; Hidden = 64; GatePrior = "0.0" }
)

foreach ($j in $jobs) {
    if ($Method -ne "all" -and $Method -ne $j.Method) { continue }
    foreach ($s in $seeds) {
        $out = "$Root/$($j.Method)/bc_seed$s"
        Write-Host "==> BC: method=$($j.Method) seed=$s out=$out"
        Invoke-BC -Python $Python -Script $j.Script -Graph $j.Graph -Hidden $j.Hidden -GatePrior $j.GatePrior -OutDir $out
    }
}

Write-Host "ALL_BC_DONE"
