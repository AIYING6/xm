#!/usr/bin/env bash
# Frozen DRTP controller: 1M, then only pre-registered common fresh 2M/3M extensions.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/drtp_sg_performance}"
MAX_PARALLEL="${MAX_PARALLEL:-4}"
EVAL_WORKERS="${EVAL_WORKERS:-4}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-16}"

if [[ "$MAX_PARALLEL" -lt 1 || "$EVAL_WORKERS" -lt 1 ]]; then
  echo "MAX_PARALLEL and EVAL_WORKERS must be positive" >&2
  exit 2
fi
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(( CPU_THREADS_TOTAL / MAX_PARALLEL ))}"
if [[ "$OMP_NUM_THREADS" -lt 1 ]]; then export OMP_NUM_THREADS=1; fi
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"

run_budget() {
  local budget="$1"
  echo "=== DRTP development ${budget}: fresh from-scratch trajectories ==="
  local running=0
  for arm in utr_sg drtp_sg; do
    for seed in 1901 1902; do
      "$PYTHON_BIN" scripts/run_drtp_sg_development_single.py \
        --arm "$arm" --seed "$seed" --budget "$budget" --output-root "$OUTPUT_ROOT" --execute \
        > "${OUTPUT_ROOT}/${budget}_${arm}_${seed}.out" \
        2> "${OUTPUT_ROOT}/${budget}_${arm}_${seed}.err" &
      running=$((running + 1))
      if [[ "$running" -ge "$MAX_PARALLEL" ]]; then
        wait -n
        running=$((running - 1))
      fi
    done
  done
  wait
  "$PYTHON_BIN" scripts/run_drtp_sg_development_evaluation.py \
    --output-root "$OUTPUT_ROOT" --budget "$budget" --workers "$EVAL_WORKERS" --execute \
    > "${OUTPUT_ROOT}/evaluation_${budget}.out" 2> "${OUTPUT_ROOT}/evaluation_${budget}.err"
  "$PYTHON_BIN" scripts/aggregate_drtp_sg_development.py \
    --results-root "$OUTPUT_ROOT" --budget "$budget" \
    > "${OUTPUT_ROOT}/aggregate_${budget}.out" 2> "${OUTPUT_ROOT}/aggregate_${budget}.err"
}

needs_extension() {
  local budget="$1"
  "$PYTHON_BIN" - "$OUTPUT_ROOT/evaluations/$budget/DRTP_DEVELOPMENT_DECISION.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as handle:
    decision = json.load(handle)
sys.exit(0 if decision["common_budget_extension_required"] else 1)
PY
}

if [[ -e "$OUTPUT_ROOT" && -n "$(find "$OUTPUT_ROOT" -mindepth 1 -print -quit)" ]]; then
  echo "Refusing to overwrite non-empty output root: $OUTPUT_ROOT" >&2
  exit 2
fi
mkdir -p "$OUTPUT_ROOT"
"$PYTHON_BIN" scripts/create_drtp_sg_development_tape.py --output-root "$OUTPUT_ROOT" --execute \
  > "${OUTPUT_ROOT}/tape_creation.out" 2> "${OUTPUT_ROOT}/tape_creation.err"

run_budget 1m
if needs_extension 1m; then
  run_budget 2m
  if needs_extension 2m; then
    run_budget 3m
  fi
fi

echo "DRTP development controller completed. Inspect the final decision before any held-out action."
