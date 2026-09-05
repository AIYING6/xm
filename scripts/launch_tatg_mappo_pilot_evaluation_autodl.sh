#!/usr/bin/env bash
# Fixed endpoint-only TATG pilot evaluation launcher. No aggregation or gate.
set -euo pipefail

: "${OUTPUT_ROOT:=results/development/tatg_mappo_pilot_v4}"
: "${WORKERS:=12}"
: "${PYTHON_BIN:=python}"
: "${OMP_NUM_THREADS:=1}"
: "${MKL_NUM_THREADS:=1}"
: "${OPENBLAS_NUM_THREADS:=1}"
: "${NUMEXPR_NUM_THREADS:=1}"
export OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS NUMEXPR_NUM_THREADS

if [ ! -f "$OUTPUT_ROOT/TATG_PILOT_TRAINING_COMPLETE.json" ]; then
  echo "completed TATG pilot training marker is required" >&2
  exit 1
fi
if [ -e "$OUTPUT_ROOT/evaluations/final_1m" ]; then
  echo "refusing to overwrite fixed endpoint evaluation" >&2
  exit 1
fi

"$PYTHON_BIN" scripts/run_tatg_mappo_pilot_evaluation.py \
  --trained-root "$OUTPUT_ROOT" \
  --output-root "$OUTPUT_ROOT/evaluations/final_1m" \
  --workers "$WORKERS" \
  --execute

printf '{"status":"TATG_PILOT_FIXED_ENDPOINT_EVALUATION_COMPLETE","training_started":false,"automatic_aggregation_or_continuation":false}\n' \
  > "$OUTPUT_ROOT/TATG_PILOT_FIXED_ENDPOINT_EVALUATION_COMPLETE.json"
