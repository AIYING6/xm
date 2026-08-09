#!/usr/bin/env bash
# Prepared launcher for an explicitly authorized AutoDL D1 engineering pilot.
# It runs serially to preserve CPU rollout capacity and does not start unless
# the operator invokes it on a CUDA instance.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python}"
OUT_ROOT="${OUT_ROOT:-results/v1_9_d1_engineering}"

"$PYTHON_BIN" scripts/check_gpu_runtime_v1_9.py --output "$OUT_ROOT/runtime_manifest.json"
"$PYTHON_BIN" scripts/test_actor_boundary_v1_8.py
"$PYTHON_BIN" scripts/test_pcrf_d0_v1_9.py

common=(
  --env-name 3d_intercept --num-envs 8 --rollout-steps 128 --updates 20
  --role-dim 8 --intent-dim 8 --ppo-epochs 4 --device cuda
  --strict-target-sensing --agent-target-info-bottleneck
  --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1
  --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80
  --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 4
  --save-interval 10 --save-snapshots --validation-event-logging
  --protocol-version V1_9_D1_ENGINEERING_PILOT
)

for seed in 9101 9102; do
  base_seed=$((2910100 + 100 * (seed - 9100)))
  "$PYTHON_BIN" scripts/train_ri_gmappo.py "${common[@]}" \
    --seed "$seed" --graph-encoder pcrf --hidden-dim 128 --eval-base-seed "$base_seed" \
    --method-label pcrf --run-id "v1_9_d1_pcrf_seed${seed}" --out-dir "$OUT_ROOT/pcrf_seed${seed}"
done

for seed in 9101 9102; do
  base_seed=$((2910100 + 100 * (seed - 9100)))
  "$PYTHON_BIN" scripts/train_ri_gmappo.py "${common[@]}" \
    --seed "$seed" --graph-encoder single --hidden-dim 168 --eval-base-seed "$base_seed" \
    --method-label wider_single_graph --run-id "v1_9_d1_single_seed${seed}" --out-dir "$OUT_ROOT/single_seed${seed}"
done

"$PYTHON_BIN" scripts/check_v1_9_d1_artifacts.py --root "$OUT_ROOT"
