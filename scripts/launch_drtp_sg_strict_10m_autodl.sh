#!/usr/bin/env bash
# Authorized 0→10M strict-continuous UTR/DRTP development controller.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/drtp_sg_strict_continuous_10m}"
MAX_PARALLEL="${MAX_PARALLEL:-4}"
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

"$PYTHON_BIN" scripts/create_drtp_sg_development_tape.py --output-root "$OUTPUT_ROOT" --execute \
  > "$OUTPUT_ROOT/tape_creation.out" 2> "$OUTPUT_ROOT/tape_creation.err"

running=0
for arm in utr_sg drtp_sg; do
  for seed in 1901 1902; do
    "$PYTHON_BIN" scripts/run_drtp_sg_strict_10m_single.py \
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

"$PYTHON_BIN" scripts/run_drtp_sg_strict_10m_evaluation.py \
  --output-root "$OUTPUT_ROOT" --workers "$EVAL_WORKERS" --execute \
  > "$OUTPUT_ROOT/evaluation_strict_10m.out" 2> "$OUTPUT_ROOT/evaluation_strict_10m.err"
"$PYTHON_BIN" scripts/aggregate_drtp_sg_strict_10m.py --results-root "$OUTPUT_ROOT" \
  > "$OUTPUT_ROOT/aggregate_strict_10m.out" 2> "$OUTPUT_ROOT/aggregate_strict_10m.err"

echo "Strict-continuous 10M development completed. Held-out and canonical work remain disabled."
