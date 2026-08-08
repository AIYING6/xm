# FORMAL_V1_8_LAUNCH_MANIFEST

**Status: launch dry-run manifest; formal training is authorized only after the
config audit below passes.** No run has been started from this manifest.

## Frozen references

- protocol commit: `e5031b6`
- packet schema: `PACKET_SCHEMA_V1_8`
- actor protocol: `FAIR_ACTOR_PROTOCOL_V1_8`
- failure: `failed_blue_agent=1`, `node_failure_start_step=40`,
  `node_failure_duration_steps=80`
- stable window: `K=4` (independent of duration 80)
- endpoint: time from failure onset to first stable task-chain establishment
- horizons: `tau=80`, `tau=220`
- validation: 20 episodes every 10 updates, base seed `10000 + 100*seed`
- budget: 8 envs, 128 rollout steps, 300 updates, PPO epochs 4, hidden 128

The three corrected methods receive the same legal recipient-specific raw
information and packet/cache semantics. Only `--graph-encoder` differs.

## Nine formal runs

Each command is intentionally explicit; no failure-duration default is used.

### Corrected EA-RG Full (`multi_relation`)

- method: corrected EA-RG Full; seed: 0; output: `results/formal_v1_8/ea_rg_seed0`
  ; git: `e5031b6`
  ; command: `python scripts/train_ri_gmappo.py --env-name 3d_intercept --seed 0 --num-envs 8 --rollout-steps 128 --updates 300 --hidden-dim 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --graph-encoder multi_relation --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 20 --eval-base-seed 10000 --save-interval 10 --out-dir results/formal_v1_8/ea_rg_seed0`
- method: corrected EA-RG Full; seed: 1; output: `results/formal_v1_8/ea_rg_seed1`
  ; git: `e5031b6`
  ; command: `python scripts/train_ri_gmappo.py --env-name 3d_intercept --seed 1 --num-envs 8 --rollout-steps 128 --updates 300 --hidden-dim 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --graph-encoder multi_relation --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 20 --eval-base-seed 10100 --save-interval 10 --out-dir results/formal_v1_8/ea_rg_seed1`
- method: corrected EA-RG Full; seed: 2; output: `results/formal_v1_8/ea_rg_seed2`
  ; git: `e5031b6`
  ; command: `python scripts/train_ri_gmappo.py --env-name 3d_intercept --seed 2 --num-envs 8 --rollout-steps 128 --updates 300 --hidden-dim 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --graph-encoder multi_relation --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 20 --eval-base-seed 10200 --save-interval 10 --out-dir results/formal_v1_8/ea_rg_seed2`

### Corrected wider single-graph (`single`)

- method: corrected wider single-graph; seed: 0; output: `results/formal_v1_8/single_seed0`
  ; git: `e5031b6`
  ; command: `python scripts/train_ri_gmappo.py --env-name 3d_intercept --seed 0 --num-envs 8 --rollout-steps 128 --updates 300 --hidden-dim 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --graph-encoder single --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 20 --eval-base-seed 10000 --save-interval 10 --out-dir results/formal_v1_8/single_seed0`
- method: corrected wider single-graph; seed: 1; output: `results/formal_v1_8/single_seed1`
  ; git: `e5031b6`
  ; command: `python scripts/train_ri_gmappo.py --env-name 3d_intercept --seed 1 --num-envs 8 --rollout-steps 128 --updates 300 --hidden-dim 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --graph-encoder single --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 20 --eval-base-seed 10100 --save-interval 10 --out-dir results/formal_v1_8/single_seed1`
- method: corrected wider single-graph; seed: 2; output: `results/formal_v1_8/single_seed2`
  ; git: `e5031b6`
  ; command: `python scripts/train_ri_gmappo.py --env-name 3d_intercept --seed 2 --num-envs 8 --rollout-steps 128 --updates 300 --hidden-dim 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --graph-encoder single --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 20 --eval-base-seed 10200 --save-interval 10 --out-dir results/formal_v1_8/single_seed2`

### Matched-information non-graph (`matched_nongraph`)

- method: matched-information non-graph; seed: 0; output: `results/formal_v1_8/matched_nongraph_seed0`
  ; git: `e5031b6`
  ; command: `python scripts/train_ri_gmappo.py --env-name 3d_intercept --seed 0 --num-envs 8 --rollout-steps 128 --updates 300 --hidden-dim 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --graph-encoder matched_nongraph --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 20 --eval-base-seed 10000 --save-interval 10 --out-dir results/formal_v1_8/matched_nongraph_seed0`
- method: matched-information non-graph; seed: 1; output: `results/formal_v1_8/matched_nongraph_seed1`
  ; git: `e5031b6`
  ; command: `python scripts/train_ri_gmappo.py --env-name 3d_intercept --seed 1 --num-envs 8 --rollout-steps 128 --updates 300 --hidden-dim 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --graph-encoder matched_nongraph --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 20 --eval-base-seed 10100 --save-interval 10 --out-dir results/formal_v1_8/matched_nongraph_seed1`
- method: matched-information non-graph; seed: 2; output: `results/formal_v1_8/matched_nongraph_seed2`
  ; git: `e5031b6`
  ; command: `python scripts/train_ri_gmappo.py --env-name 3d_intercept --seed 2 --num-envs 8 --rollout-steps 128 --updates 300 --hidden-dim 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --graph-encoder matched_nongraph --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 20 --eval-base-seed 10200 --save-interval 10 --out-dir results/formal_v1_8/matched_nongraph_seed2`

## Stop-after-training rule

Run only training and frozen validation. After all nine runs, report completion,
crash/NaN/boundary status, learning curves, AUC diagnostics, selected update,
validation RMST80, establishment/censoring, RMST220, seed variability, measured
time, and deviations. Stop before confirmatory held-out evaluation, OOD,
relation-conflict performance evaluation, ablations, or manuscript edits.
