#!/usr/bin/env bash
# Frozen F1-R2 formal training only.  This script never evaluates F2.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUT_ROOT="${OUT_ROOT:-results/v1_9_f1_r2_formal}"
EXPECTED_SOURCE_COMMIT="${EXPECTED_SOURCE_COMMIT:?set full source commit}"
PROTOCOL="V1_9_F1_R2_FORMAL_TRAINING"
export OMP_NUM_THREADS=1

[[ "$(git rev-parse HEAD)" == "$EXPECTED_SOURCE_COMMIT" ]] || { echo "source commit mismatch" >&2; exit 2; }
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || { echo "tracked source tree is dirty" >&2; exit 2; }
[[ ! -e "$OUT_ROOT" ]] || { echo "refusing to reuse formal output root: $OUT_ROOT" >&2; exit 2; }

"$PYTHON_BIN" - <<'PY'
import torch
if not torch.cuda.is_available() or torch.cuda.get_device_properties(0).total_memory < 16 * 1024**3:
    raise SystemExit("F1-R2 requires CUDA GPU memory >=16 GiB")
print(torch.cuda.get_device_name(0))
PY

mkdir -p "$OUT_ROOT"
"$PYTHON_BIN" scripts/check_gpu_runtime_v1_9.py --output "$OUT_ROOT/runtime_manifest.json" --protocol-version "$PROTOCOL"
for test in scripts/test_actor_boundary_v1_8.py scripts/test_pcrf_r2_d0_v1_9.py scripts/test_p0_a_terminal_estimand_v1_9.py scripts/audit_p1_onset_state_v1_9.py scripts/audit_p1_endpoint_construct_validity_v1_9.py scripts/audit_p1_independent_mission_outcome_v1_9.py; do
  "$PYTHON_BIN" "$test"
done

common=(--env-name 3d_intercept --num-envs 8 --rollout-steps 128 --role-dim 8 --intent-dim 8 --ppo-epochs 4 --device cuda
  --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.3 --message-delay-steps 2 --radar-dropout-prob 0.1
  --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --attack-hold-steps 4 --min-success-step 80
  --updates 300 --eval-interval 10 --eval-episodes 16 --eval-base-seed 410000 --save-interval 10 --save-snapshots --validation-event-logging --protocol-version "$PROTOCOL")

run_one () {
  local method="$1" encoder="$2" hidden="$3" seed="$4"
  local run_dir="$OUT_ROOT/${method}_seed${seed}"
  mkdir -p "$run_dir"
  "$PYTHON_BIN" scripts/train_ri_gmappo.py "${common[@]}" --seed "$seed" --graph-encoder "$encoder" --hidden-dim "$hidden" --method-label "$method" --run-id "v1_9_f1_r2_${method}_seed${seed}" --out-dir "$run_dir" >"$run_dir/train.stdout.log" 2>"$run_dir/train.stderr.log"
}

for seed in 0 1 2 3 4 5 6 7; do
  run_one pcrf_r2 pcrf_r2 128 "$seed"
  run_one single_r2 single_r2 147 "$seed"
  run_one matched_nongraph_r2 matched_nongraph_r2 152 "$seed"
done

"$PYTHON_BIN" scripts/check_v1_9_f1_r2_artifacts.py --root "$OUT_ROOT" --expected-source-commit "$EXPECTED_SOURCE_COMMIT" --output "$OUT_ROOT/F1_R2_TRAINING_ARTIFACT_GATE_MANIFEST.json"
"$PYTHON_BIN" scripts/select_v1_9_f1_r2_checkpoints.py --root "$OUT_ROOT" --expected-source-commit "$EXPECTED_SOURCE_COMMIT" --output "$OUT_ROOT/F1_R2_SELECTED_CHECKPOINTS_MANIFEST.json"
