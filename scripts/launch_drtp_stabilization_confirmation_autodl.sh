#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/confirmatory/drtp_stabilization_final_confirmation}"
MAX_PARALLEL="${MAX_PARALLEL:-18}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-20}"
COHORT="${COHORT:-A}"

[[ "$MAX_PARALLEL" -ge 1 && "$MAX_PARALLEL" -le 20 ]] || { echo "MAX_PARALLEL must be 1..20" >&2; exit 2; }
[[ "$COHORT" == "A" || "$COHORT" == "B" ]] || { echo "COHORT must be A or B" >&2; exit 2; }
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(( CPU_THREADS_TOTAL / MAX_PARALLEL ))}"
[[ "$OMP_NUM_THREADS" -ge 1 ]] || export OMP_NUM_THREADS=1
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-$OMP_NUM_THREADS}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-$OMP_NUM_THREADS}"

[[ ! -e "$OUTPUT_ROOT/runs" ]] || { echo "confirmation runs already exist: $OUTPUT_ROOT/runs" >&2; exit 2; }
mkdir -p "$OUTPUT_ROOT"
[[ -f "$OUTPUT_ROOT/preflight/CONFIRMATORY_PREFLIGHT.json" ]] || "$PYTHON_BIN" scripts/verify_drtp_stabilization_confirmation_preflight.py --cohort "$COHORT" --output-root "$OUTPUT_ROOT/preflight" --execute > "$OUTPUT_ROOT/preflight.out"
"$PYTHON_BIN" scripts/create_drtp_stabilization_confirmatory_tape.py --cohort "$COHORT" --output-root "$OUTPUT_ROOT/tape" > "$OUTPUT_ROOT/tape.out"

running=0
if [[ "$COHORT" == "A" ]]; then
  SEEDS=(78011 78012 78013 78014 78015)
else
  SEEDS=(78021 78022 78023 78024 78025)
fi
for arm in utr_sg drtp_sg egtr_sg global_anchored_egtr_a075_sg; do
  for seed in "${SEEDS[@]}"; do
    "$PYTHON_BIN" scripts/run_drtp_stabilization_confirmatory_single.py --cohort "$COHORT" --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/${arm}_${seed}.out" 2> "$OUTPUT_ROOT/${arm}_${seed}.err" &
    running=$((running + 1))
    if [[ "$running" -ge "$MAX_PARALLEL" ]]; then wait -n; running=$((running - 1)); fi
  done
done
wait
printf '{"status":"DRTP_STABILIZATION_COHORT_%s_TRAINING_COMPLETE","cohort":"%s","trajectories":20,"evaluation_started":false,"automatic_algorithm_revision":false}\n' "$COHORT" "$COHORT" > "$OUTPUT_ROOT/CONFIRMATION_TRAINING_COMPLETE.json"
"$PYTHON_BIN" scripts/run_drtp_stabilization_confirmatory_evaluation.py --cohort "$COHORT" --trained-root "$OUTPUT_ROOT" --output-root "$OUTPUT_ROOT/evaluations/final_10m" --workers "$MAX_PARALLEL" --execute
"$PYTHON_BIN" scripts/aggregate_drtp_stabilization_confirmation.py --cohort "$COHORT" --trained-root "$OUTPUT_ROOT" --evaluation-root "$OUTPUT_ROOT/evaluations/final_10m" --output-root "$OUTPUT_ROOT" --execute
printf '{"status":"DRTP_STABILIZATION_COHORT_%s_COMPLETE","cohort":"%s","trajectories":20,"endpoint_evaluation_completed":true,"automatic_algorithm_revision":false,"automatic_6uav":false}\n' "$COHORT" "$COHORT" > "$OUTPUT_ROOT/CONFIRMATION_COMPLETE.json"
echo "Frozen cohort $COHORT complete. No algorithm revision or 6-UAV run was started automatically."
