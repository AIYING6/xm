# Regenerate BC initializations for the new post-sixth-freeze v1 baseline.
# Must run AFTER the env P0 fix (zero/mask on target prior + union-graph attack-edge removal)
# and BEFORE any PPO training. Same demonstration protocol as the frozen BC rule:
#   teacher=geometric offset, episodes=120, epochs=20, batch=256, balanced loss, attacker weight=2.0.
#
# Formal protocol gates enforced here:
#   1. HEAD must equal the freeze tag commit and the tracked tree must be clean.
#   2. Existing BC outputs are never silently overwritten (use -Force to override).
#   3. Every BC directory gets a bc_manifest.json recording the freeze commit.
param(
    [string]$Python = "python",
    [string]$Root = "results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802",
    [ValidateSet("all", "no_graph", "single_graph", "param_matched_single", "ea_rg_mappo_s_gate_prior", "happo")]
    [string]$Method = "all",
    [ValidateSet(0, 1, 2, 99)]
    [int]$Seed = 99,
    [string]$ExpectedTag = "formal-post-sixth-ops-v1.4.0",
    [string]$ExpectedBCTag = "formal-post-sixth-freeze-v1.4",
    # Overwrite existing BC outputs. Produces non-formal evidence unless the
    # previous outputs were deliberately discarded first.
    [switch]$Force,
    # Escape hatch for development smoke runs. Outputs are NOT formal evidence.
    [switch]$AllowUnfrozen,
    # Safe resume after interruption: skip BCs whose directory already exists AND
    # passes the full verification gate (manifest + SHA256 + architecture).
    # BCs that exist but fail verification still BLOCK.
    [switch]$ResumeValid
)

$ErrorActionPreference = "Stop"

. "$PSScriptRoot/formal_freeze_gate.ps1"

# ---- Gate 1: git freeze (ops tag) --------------------------------------------
$null = Assert-FrozenWorkspace -ExpectedTag $ExpectedTag -AllowUnfrozen:$AllowUnfrozen

# ---- BC provenance commit (algorithm tag) ------------------------------------
$BCFreezeCommit = (& git rev-list -n 1 $ExpectedBCTag 2>$null).Trim()
if (-not $BCFreezeCommit) {
    Write-Error "BLOCKED: cannot resolve BC provenance tag '$ExpectedBCTag'"
    exit 2
}

function Test-BCOutputExists {
    param([string]$OutDir)
    return (
        (Test-Path "$OutDir/bc_train_log.csv") -or
        (Test-Path "$OutDir/actor_critic_latest.pt") -or
        (Test-Path "$OutDir/happo_bc_latest.pt")
    )
}

function Write-BCManifest {
    param(
        [string]$OutDir,
        [string]$MethodName,
        [int]$SeedValue,
        [string]$Graph,
        [int]$Hidden,
        [string]$GatePrior,
        [string]$FreezeCommit,
        [string]$ExpectedTag
    )
    $ckpt = if ($MethodName -eq "happo") { "happo_bc_latest.pt" } else { "actor_critic_latest.pt" }
    $ckptPath = Join-Path $OutDir $ckpt
    $sha = ""
    if (Test-Path $ckptPath) {
        $sha = (Get-FileHash -Algorithm SHA256 -Path $ckptPath).Hash.ToLower()
    }
    $manifest = [ordered]@{
        method                   = $MethodName
        seed                     = $SeedValue
        freeze_tag               = $ExpectedTag
        freeze_commit            = $FreezeCommit
        graph_encoder            = $Graph
        hidden_dim               = $Hidden
        role_gate_prior_strength = [double]$GatePrior
        role_dim                 = 8
        intent_dim               = 8
        episodes                 = 120
        epochs                   = 20
        batch_size               = 256
        teacher                  = "geometric_offset"
        attacker_action_weight   = 2.0
        checkpoint               = $ckpt
        checkpoint_sha256        = $sha
        generated_at_utc         = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    $json = $manifest | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText(
        (Join-Path $OutDir "bc_manifest.json"),
        $json,
        [System.Text.UTF8Encoding]::new($false)
    )
}

function Invoke-BC {
    param(
        [string]$Python,
        [string]$Script,
        [string]$Graph,
        [int]$Hidden,
        [string]$GatePrior,
        [int]$SeedValue,
        [string]$OutDir
    )
    & $Python $Script `
        --episodes 120 --epochs 20 --batch-size 256 `
        --hidden-dim $Hidden --role-dim 8 --intent-dim 8 `
        --graph-encoder $Graph `
        --role-gate-prior-strength $GatePrior `
        --geometric-policy-mode offset --attacker-action-weight 2.0 `
        --seed $SeedValue --target-policy straight `
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

# ---- Gate 2: refuse to overwrite existing BC outputs (pre-flight, all jobs) --
$planned = @()
foreach ($j in $jobs) {
    if ($Method -ne "all" -and $Method -ne $j.Method) { continue }
    foreach ($s in $seeds) {
        $planned += @{ Job = $j; SeedValue = $s; OutDir = "$Root/$($j.Method)/bc_seed$s" }
    }
}
if ($planned.Count -eq 0) {
    Write-Error "BLOCKED: no BC jobs selected (method=$Method seed=$Seed)"
    exit 2
}

$collisions = @($planned | Where-Object { Test-BCOutputExists -OutDir $_.OutDir })
if ($collisions.Count -gt 0 -and -not $Force -and -not $ResumeValid) {
    foreach ($c in $collisions) {
        Write-Error "BLOCKED: BC output already exists: $($c.OutDir)"
    }
    Write-Error "Refusing to overwrite $($collisions.Count) existing BC output(s). Remove them or pass -Force."
    exit 2
}

# When -ResumeValid: verify each existing BC; skip if fully valid, BLOCK if invalid.
$skipList = @()
if ($ResumeValid -and $collisions.Count -gt 0) {
    foreach ($c in $collisions) {
        Write-Host "ResumeValid check: $($c.OutDir)"
        & $Python "scripts/verify_bc_checkpoint.py" `
            --root $Root `
            --method $($c.Job.Method) `
            --seed $($c.SeedValue) `
            --expected-tag $ExpectedBCTag
        if ($LASTEXITCODE -ne 0) {
            Write-Error "BLOCKED: existing BC at $($c.OutDir) failed verification; remove it or inspect manually."
            exit 2
        }
        $skipList += $c
        Write-Host "  -> SKIP (already valid)"
    }
}

$toRun = @($planned | Where-Object { $skipList -notcontains $_ })

foreach ($p in $toRun) {
    $j = $p.Job
    $out = $p.OutDir
    Write-Host "==> BC: method=$($j.Method) seed=$($p.SeedValue) out=$out"
    Invoke-BC -Python $Python -Script $j.Script -Graph $j.Graph -Hidden $j.Hidden `
        -GatePrior $j.GatePrior -SeedValue $p.SeedValue -OutDir $out
    Write-BCManifest -OutDir $out -MethodName $j.Method -SeedValue $p.SeedValue `
        -Graph $j.Graph -Hidden $j.Hidden -GatePrior $j.GatePrior `
        -FreezeCommit $BCFreezeCommit -ExpectedTag $ExpectedBCTag
}

# ---- Post-check: verify ONLY the tasks just produced (not all 15) -------------
if ($toRun.Count -gt 0) {
    Write-Host "==> Verifying BC checkpoints ($($toRun.Count) task(s))"
    foreach ($p in $toRun) {
        & $Python "scripts/verify_bc_checkpoint.py" `
            --root $Root `
            --method $($p.Job.Method) `
            --seed $($p.SeedValue) `
            --expected-tag $ExpectedBCTag
        if ($LASTEXITCODE -ne 0) {
            Write-Error "BLOCKED: BC verification failed for $($p.Job.Method) seed$($p.SeedValue)"
            exit 2
        }
    }
} else {
    Write-Host "==> No new BC tasks to verify (all already valid)."
}

Write-Host "ALL_BC_DONE"
