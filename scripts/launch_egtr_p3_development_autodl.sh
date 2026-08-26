#!/usr/bin/env bash
# Frozen EGTR P3: UTR/DRTP/EGTR x seeds 2501/2502/2503, 1M only.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/egtr_p3}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-16}"

if [[ "$MAX_PARALLEL" -lt 1 ]]; then
  echo "MAX_PARALLEL must be positive" >&2
  exit 2
fi
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(( CPU_THREADS_TOTAL / MAX_PARALLEL ))}"
if [[ "$OMP_NUM_THREADS" -lt 1 ]]; then export OMP_NUM_THREADS=1; fi
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"

if [[ -e "$OUTPUT_ROOT" && -n "$(find "$OUTPUT_ROOT" -mindepth 1 -print -quit)" ]]; then
  echo "Refusing to overwrite non-empty output root: $OUTPUT_ROOT" >&2
  exit 2
fi
mkdir -p "$OUTPUT_ROOT"

"$PYTHON_BIN" scripts/verify_egtr_p3_preflight.py --output-root "$OUTPUT_ROOT" --execute \
  > "$OUTPUT_ROOT/preflight.out" 2> "$OUTPUT_ROOT/preflight.err"

running=0
for arm in utr_sg drtp_sg egtr_sg; do
  for seed in 2501 2502 2503; do
    "$PYTHON_BIN" scripts/run_egtr_p3_development_single.py \
      --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute \
      > "$OUTPUT_ROOT/${arm}_${seed}.out" \
      2> "$OUTPUT_ROOT/${arm}_${seed}.err" &
    running=$((running + 1))
    if [[ "$running" -ge "$MAX_PARALLEL" ]]; then
      wait -n
      running=$((running - 1))
    fi
  done
done
wait

echo "EGTR P3 1M training completed. No evaluation or 3M continuation is started by this launcher."
