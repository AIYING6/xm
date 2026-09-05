#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/drtp_stabilization_development_v1}"
MAX_PARALLEL="${MAX_PARALLEL:-12}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-12}"

if [[ "$MAX_PARALLEL" -lt 1 ]]; then echo "MAX_PARALLEL must be positive" >&2; exit 2; fi
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(( CPU_THREADS_TOTAL / MAX_PARALLEL ))}"
if [[ "$OMP_NUM_THREADS" -lt 1 ]]; then export OMP_NUM_THREADS=1; fi
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-$OMP_NUM_THREADS}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-$OMP_NUM_THREADS}"

if [[ -e "$OUTPUT_ROOT/runs" && -n "$(find "$OUTPUT_ROOT/runs" -mindepth 1 -print -quit)" ]]; then
  echo "Refusing to overwrite existing V1 training runs: $OUTPUT_ROOT/runs" >&2; exit 2
fi
mkdir -p "$OUTPUT_ROOT"
"$PYTHON_BIN" scripts/create_drtp_stabilization_development_v1_tape.py --output-root "$OUTPUT_ROOT/tape" > "$OUTPUT_ROOT/tape.out"

running=0
for arm in utr_sg drtp_sg egtr_sg anchored_egtr_a035_sg anchored_egtr_a055_sg anchored_egtr_a075_sg; do
  for seed in 76011 76012 76013; do
    "$PYTHON_BIN" scripts/run_drtp_stabilization_development_v1_single.py --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/${arm}_${seed}.out" 2> "$OUTPUT_ROOT/${arm}_${seed}.err" &
    running=$((running + 1))
    if [[ "$running" -ge "$MAX_PARALLEL" ]]; then wait -n; running=$((running - 1)); fi
  done
done
wait
printf '%s\n' '{"status":"DRTP_STABILIZATION_DEVELOPMENT_V1_TRAINING_COMPLETE","trajectories":18,"evaluation_started":false,"automatic_continuation":false}' > "$OUTPUT_ROOT/DEVELOPMENT_V1_TRAINING_COMPLETE.json"
"$PYTHON_BIN" scripts/run_drtp_stabilization_development_v1_evaluation.py \
  --trained-root "$OUTPUT_ROOT" \
  --output-root "$OUTPUT_ROOT/evaluations/final_1m" \
  --workers "$MAX_PARALLEL" \
  --execute
"$PYTHON_BIN" scripts/aggregate_drtp_stabilization_development_v1.py \
  --trained-root "$OUTPUT_ROOT" \
  --evaluation-root "$OUTPUT_ROOT/evaluations/final_1m" \
  --output-root "$OUTPUT_ROOT" \
  --execute
printf '%s\n' '{"status":"DRTP_STABILIZATION_DEVELOPMENT_V1_COMPLETE","trajectories":18,"endpoint_evaluation_completed":true,"integrated_development_assessment_completed":true,"automatic_v2_or_confirmation":false}' > "$OUTPUT_ROOT/DEVELOPMENT_V1_COMPLETE.json"
echo "V1 training, fixed endpoint evaluation, and integrated development assessment complete. No V2 or confirmation was started automatically."
