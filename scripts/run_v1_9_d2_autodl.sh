#!/usr/bin/env bash
# Prepared launcher for the non-formal v1.9 D2-R1 PCRF budget calibration.
set -euo pipefail

echo "PCRF-R1 D2 is terminated by the G0-R1 author decision. Use no GPU and do not relaunch this historical script." >&2
exit 2

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python}"
OUT_ROOT="${OUT_ROOT:-results/v1_9_d2_budget_calibration_r1}"
SOURCE_COMMIT="${SOURCE_COMMIT:?Set SOURCE_COMMIT to the immutable source commit before launch}"
SOURCE_ARCHIVE_SHA256="${SOURCE_ARCHIVE_SHA256:?Set SOURCE_ARCHIVE_SHA256 to the exact uploaded source archive SHA256 before launch}"

mkdir -p "$OUT_ROOT"
telemetry="$OUT_ROOT/gpu_telemetry.csv"
if [[ -e "$telemetry" ]]; then
  echo "Refusing to overwrite existing D2 telemetry: $telemetry" >&2
  exit 2
fi
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total \
  --format=csv,noheader,nounits -l 10 > "$telemetry" &
TELEMETRY_PID=$!
trap 'kill "$TELEMETRY_PID" 2>/dev/null || true' EXIT

"$PYTHON_BIN" scripts/check_gpu_runtime_v1_9.py \
  --output "$OUT_ROOT/runtime_manifest.json" \
  --protocol-version V1_9_D2_BUDGET_CALIBRATION_R1 \
  --source-commit "$SOURCE_COMMIT" \
  --source-archive-sha256 "$SOURCE_ARCHIVE_SHA256"
"$PYTHON_BIN" scripts/test_actor_boundary_v1_8.py
"$PYTHON_BIN" scripts/test_pcrf_d0_v1_9.py

common=(
  --env-name 3d_intercept --num-envs 8 --rollout-steps 128 --updates 100
  --role-dim 8 --intent-dim 8 --ppo-epochs 4 --device cuda
  --strict-target-sensing --agent-target-info-bottleneck
  --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1
  --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80
  --attack-hold-steps 4 --min-success-step 80 --eval-interval 20 --eval-episodes 8
  --save-interval 20 --save-snapshots --validation-event-logging
  --protocol-version V1_9_D2_BUDGET_CALIBRATION_R1
)

for seed in 9201 9202 9203; do
  base_seed=$((2920100 + 100 * (seed - 9200)))
  run_dir="$OUT_ROOT/pcrf_seed${seed}"
  mkdir -p "$run_dir"
  "$PYTHON_BIN" scripts/run_with_timing_v1_9.py --output "$run_dir/runtime_timing.json" -- \
    "$PYTHON_BIN" scripts/train_ri_gmappo.py "${common[@]}" \
      --seed "$seed" --graph-encoder pcrf --hidden-dim 128 --eval-base-seed "$base_seed" \
      --method-label pcrf --run-id "v1_9_d2_pcrf_seed${seed}" --out-dir "$run_dir"
done

kill "$TELEMETRY_PID" 2>/dev/null || true
wait "$TELEMETRY_PID" 2>/dev/null || true
trap - EXIT
"$PYTHON_BIN" scripts/check_v1_9_d2_artifacts.py --root "$OUT_ROOT"
