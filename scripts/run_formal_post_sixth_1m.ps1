param(
    [string]$Python = "D:/Anaconda/envs/.conda/envs/cac/python.exe",
    [string]$Device = "cpu",
    [int]$Updates = 977
)

$ErrorActionPreference = "Stop"

$Root = "results/paper_config_runs/formal_budget_post_sixth_freeze"
$Seeds = @(0, 1, 2)

$RiMethods = @(
    @{ Method = "no_graph"; Graph = "no_graph"; Hidden = 64; GatePrior = "0.0" },
    @{ Method = "single_graph"; Graph = "single"; Hidden = 64; GatePrior = "0.0" },
    @{ Method = "param_matched_single"; Graph = "single"; Hidden = 96; GatePrior = "0.0" },
    @{ Method = "ea_rg_mappo_s_gate_prior"; Graph = "multi_relation"; Hidden = 64; GatePrior = "0.4" }
)

function Assert-NewOutputDir {
    param([string]$Path)
    if (Test-Path $Path) {
        throw "Refusing to overwrite existing formal output directory: $Path"
    }
}

function Run-RiPpo {
    param(
        [hashtable]$Spec,
        [int]$Seed
    )
    $method = $Spec.Method
    $outDir = "$Root/$method/ppo_seed${Seed}_1m"
    $init = "$Root/$method/bc_seed$Seed/actor_critic_latest.pt"
    Assert-NewOutputDir $outDir
    Write-Host "Running RI PPO: method=$method seed=$Seed updates=$Updates"
    & $Python scripts/train_ri_gmappo.py `
        --env-name 3d_intercept `
        --seed $Seed --num-envs 8 --rollout-steps 128 --updates $Updates `
        --hidden-dim $Spec.Hidden --role-dim 8 --intent-dim 8 `
        --graph-encoder $Spec.Graph `
        --role-gate-prior-strength $Spec.GatePrior `
        --init-checkpoint $init `
        --actor-lr 5e-5 --critic-lr 1e-4 `
        --clip-coef 0.1 --ppo-epochs 2 --target-kl 0.01 `
        --entropy-coef 0.003 --max-grad-norm 0.5 --critic-warmup-updates 20 `
        --eval-interval 100 --eval-episodes 5 --eval-base-seed 391000 `
        --save-interval 100 --save-snapshots `
        --target-policy straight `
        --strict-target-sensing --agent-target-info-bottleneck `
        --communication-dropout-prob 0.30 --message-delay-steps 2 `
        --failed-blue-agent 1 `
        --node-failure-start-random-min 25 --node-failure-start-random-max 70 `
        --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 `
        --post-loss-chain-reclosure-reward-weight 0.5 `
        --post-loss-chain-reclosure-min-step 80 `
        --safety-proximity-distance 2500 `
        --safety-proximity-penalty-weight 0.5 `
        --device $Device `
        --out-dir $outDir
}

function Run-HappoPpo {
    param([int]$Seed)
    $outDir = "$Root/happo/ppo_seed${Seed}_1m"
    $init = "$Root/happo/bc_seed$Seed/happo_bc_latest.pt"
    Assert-NewOutputDir $outDir
    Write-Host "Running HAPPO PPO: seed=$Seed updates=$Updates"
    & $Python scripts/train_happo_baseline.py `
        --seed $Seed --num-envs 8 --rollout-steps 128 --updates $Updates `
        --hidden-dim 64 --role-dim 8 --intent-dim 8 `
        --init-checkpoint $init `
        --lr 5e-5 --clip-coef 0.1 --ppo-epochs 2 `
        --entropy-coef 0.003 --max-grad-norm 0.5 `
        --eval-interval 100 --eval-episodes 5 --eval-base-seed 391000 `
        --save-interval 100 --save-snapshots `
        --target-policy straight `
        --strict-target-sensing --agent-target-info-bottleneck `
        --communication-dropout-prob 0.30 --message-delay-steps 2 `
        --failed-blue-agent 1 `
        --node-failure-start-random-min 25 --node-failure-start-random-max 70 `
        --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 `
        --safety-proximity-distance 2500 `
        --safety-proximity-penalty-weight 0.5 `
        --device $Device `
        --out-dir $outDir
}

foreach ($seed in $Seeds) {
    foreach ($spec in $RiMethods) {
        Run-RiPpo -Spec $spec -Seed $seed
    }
    Run-HappoPpo -Seed $seed
}

Write-Host "Formal post-sixth 1M PPO run complete."
