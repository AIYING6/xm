#!/usr/bin/env bash
# Frozen cross-scale formal run: no curriculum, early stop, rerun, or mutation.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/final_evidence/drtp_6uav_cross_scale_formal}"
MAX_PARALLEL="${MAX_PARALLEL:-10}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-12}"

[[ "$MAX_PARALLEL" =~ ^[0-9]+$ && "$MAX_PARALLEL" -ge 1 && "$MAX_PARALLEL" -le 20 ]] || { echo "MAX_PARALLEL must be 1..20" >&2; exit 2; }
[[ "$CPU_THREADS_TOTAL" =~ ^[0-9]+$ && "$CPU_THREADS_TOTAL" -ge 1 ]] || { echo "CPU_THREADS_TOTAL must be positive" >&2; exit 2; }
[[ ! -e "$OUTPUT_ROOT/runs" ]] || { echo "refusing to overwrite formal runs: $OUTPUT_ROOT/runs" >&2; exit 2; }

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(( CPU_THREADS_TOTAL / MAX_PARALLEL ))}"
[[ "$OMP_NUM_THREADS" -ge 1 ]] || export OMP_NUM_THREADS=1
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-$OMP_NUM_THREADS}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-$OMP_NUM_THREADS}"
mkdir -p "$OUTPUT_ROOT/launcher_logs"

"$PYTHON_BIN" scripts/verify_drtp_plr_and_6uav_formal_preflight.py --line 6uav --output-root "$OUTPUT_ROOT/preflight" --execute

run_train() {
  local arm="$1" seed="$2"
  "$PYTHON_BIN" scripts/run_drtp_6uav_cross_scale_formal.py train --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute \
    > "$OUTPUT_ROOT/launcher_logs/train_${arm}_seed${seed}.out" 2> "$OUTPUT_ROOT/launcher_logs/train_${arm}_seed${seed}.err"
}
for arm in utr_scout_terminal_assigned_role_sg_mappo drtp_scout_terminal_assigned_role_sg_mappo; do
  for seed in 69011 69012 69013 69014 69015; do
    while [[ "$(jobs -rp | wc -l)" -ge "$MAX_PARALLEL" ]]; do wait -n; done
    run_train "$arm" "$seed" &
  done
done
wait
printf '{"status":"DRTP_6UAV_CROSS_SCALE_TRAINING_COMPLETE","trajectories":10,"evaluation_started":false,"automatic_algorithm_revision":false}\n' > "$OUTPUT_ROOT/DRTP_6UAV_TRAINING_COMPLETE.json"

run_eval() {
  local arm="$1" seed="$2"
  "$PYTHON_BIN" scripts/run_drtp_6uav_cross_scale_formal.py evaluate --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute \
    > "$OUTPUT_ROOT/launcher_logs/evaluate_${arm}_seed${seed}.out" 2> "$OUTPUT_ROOT/launcher_logs/evaluate_${arm}_seed${seed}.err"
}
for arm in utr_scout_terminal_assigned_role_sg_mappo drtp_scout_terminal_assigned_role_sg_mappo; do
  for seed in 69011 69012 69013 69014 69015; do
    while [[ "$(jobs -rp | wc -l)" -ge "$MAX_PARALLEL" ]]; do wait -n; done
    run_eval "$arm" "$seed" &
  done
done
wait
"$PYTHON_BIN" scripts/run_drtp_6uav_cross_scale_formal.py aggregate --output-root "$OUTPUT_ROOT" --execute
printf '{"status":"DRTP_6UAV_CROSS_SCALE_COMPLETE","trajectories":10,"endpoint_evaluation_completed":true,"automatic_algorithm_revision":false,"automatic_continuation":false}\n' > "$OUTPUT_ROOT/DRTP_6UAV_CROSS_SCALE_COMPLETE.json"
echo "6-UAV cross-scale formal run complete; no algorithm revision was started."
