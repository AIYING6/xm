#!/usr/bin/env bash
# D1-R2 engineering-only launcher.  Do not use its output for performance claims.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python}"
OUT_ROOT="${OUT_ROOT:-results/v1_9_d1_r2_engineering}"
PROTOCOL="V1_9_D1_R2_ENGINEERING_PILOT"
EXPECTED_SOURCE_COMMIT="${EXPECTED_SOURCE_COMMIT:?Set the exact Git commit approved for D1-R2.}"
export OMP_NUM_THREADS=1

actual_commit="$(git rev-parse HEAD)"
if [[ "$actual_commit" != "$EXPECTED_SOURCE_COMMIT" ]]; then
  echo "D1-R2 refuses source mismatch: expected $EXPECTED_SOURCE_COMMIT, found $actual_commit" >&2
  exit 2
fi
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "D1-R2 requires a clean tracked source checkout." >&2
  exit 2
fi

"$PYTHON_BIN" scripts/check_gpu_runtime_v1_9.py \
  --output "$OUT_ROOT/runtime_manifest.json" --protocol-version "$PROTOCOL"
"$PYTHON_BIN" scripts/test_actor_boundary_v1_8.py
"$PYTHON_BIN" scripts/test_pcrf_r2_d0_v1_9.py

common=(
  --env-name 3d_intercept --num-envs 8 --rollout-steps 128
  --role-dim 8 --intent-dim 8 --ppo-epochs 4 --device cuda
  --strict-target-sensing --agent-target-info-bottleneck
  --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1
  --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80
  --attack-hold-steps 4 --min-success-step 80 --eval-interval 10 --eval-episodes 4
  --save-interval 10 --save-snapshots --validation-event-logging
  --protocol-version "$PROTOCOL"
)

run_one() {
  local method="$1" encoder="$2" hidden="$3" seed="$4" eval_seed="$5"
  local run_dir="$OUT_ROOT/${method}_seed${seed}"
  local run_id="v1_9_d1_r2_${method}_seed${seed}"
  mkdir -p "$run_dir"
  "$PYTHON_BIN" scripts/train_ri_gmappo.py "${common[@]}" \
    --updates 10 --seed "$seed" --graph-encoder "$encoder" --hidden-dim "$hidden" \
    --eval-base-seed "$eval_seed" --method-label "$method" --run-id "$run_id" \
    --out-dir "$run_dir" >"$run_dir/segment_01_10.stdout.log" 2>"$run_dir/segment_01_10.stderr.log"
  "$PYTHON_BIN" scripts/train_ri_gmappo.py "${common[@]}" \
    --updates 20 --update-offset 10 --append-log \
    --resume "$run_dir/actor_critic_training_state_latest.pt" \
    --seed "$seed" --graph-encoder "$encoder" --hidden-dim "$hidden" \
    --eval-base-seed "$eval_seed" --method-label "$method" --run-id "$run_id" \
    --out-dir "$run_dir" >"$run_dir/segment_11_30.stdout.log" 2>"$run_dir/segment_11_30.stderr.log"
}

for seed in 9201 9202; do
  eval_seed=$((2920100 + 100 * (seed - 9200)))
  run_one pcrf_r2 pcrf_r2 128 "$seed" "$eval_seed"
  run_one single_r2 single_r2 147 "$seed" "$eval_seed"
  run_one matched_nongraph_r2 matched_nongraph_r2 152 "$seed" "$eval_seed"
done

"$PYTHON_BIN" scripts/check_v1_9_d1_r2_artifacts.py \
  --root "$OUT_ROOT" --expected-source-commit "$EXPECTED_SOURCE_COMMIT" \
  --output "$OUT_ROOT/D1_R2_ARTIFACT_GATE_MANIFEST.json"
