#!/usr/bin/env bash
# Authorized DRTP-SG-MAPPO held-out confirmation v2 controller only.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/heldout/drtp_sg_heldout_v2}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
EVAL_WORKERS="${EVAL_WORKERS:-8}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-16}"

if [[ "$MAX_PARALLEL" -lt 1 || "$EVAL_WORKERS" -lt 1 ]]; then
  echo "MAX_PARALLEL and EVAL_WORKERS must be positive" >&2
  exit 2
fi
if [[ -e "$OUTPUT_ROOT" && -n "$(find "$OUTPUT_ROOT" -mindepth 1 -print -quit)" ]]; then
  echo "Refusing to overwrite non-empty output root: $OUTPUT_ROOT" >&2
  exit 2
fi
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(( CPU_THREADS_TOTAL / MAX_PARALLEL ))}"
if [[ "$OMP_NUM_THREADS" -lt 1 ]]; then export OMP_NUM_THREADS=1; fi
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"
mkdir -p "$OUTPUT_ROOT"

"$PYTHON_BIN" scripts/create_drtp_sg_heldout_v2_tape.py --output-root "$OUTPUT_ROOT" --execute \
  > "$OUTPUT_ROOT/tape_creation.out" 2> "$OUTPUT_ROOT/tape_creation.err"

running=0
for arm in utr_sg drtp_sg; do
  for seed in 2001 2002 2003; do
    "$PYTHON_BIN" scripts/run_drtp_sg_heldout_v2_single.py \
      --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute \
      > "$OUTPUT_ROOT/${arm}_${seed}.out" 2> "$OUTPUT_ROOT/${arm}_${seed}.err" &
    running=$((running + 1))
    if [[ "$running" -ge "$MAX_PARALLEL" ]]; then
      wait -n
      running=$((running - 1))
    fi
  done
done
wait

"$PYTHON_BIN" scripts/run_drtp_sg_heldout_v2_evaluation.py \
  --output-root "$OUTPUT_ROOT" --workers "$EVAL_WORKERS" --execute \
  > "$OUTPUT_ROOT/evaluation_heldout_v2.out" 2> "$OUTPUT_ROOT/evaluation_heldout_v2.err"
"$PYTHON_BIN" scripts/aggregate_drtp_sg_heldout_v2.py --results-root "$OUTPUT_ROOT" \
  > "$OUTPUT_ROOT/aggregate_heldout_v2.out" 2> "$OUTPUT_ROOT/aggregate_heldout_v2.err"

echo "Held-out v2 controller completed. No canonical, formal five-seed, ablation, or follow-on OOD stage was started."
