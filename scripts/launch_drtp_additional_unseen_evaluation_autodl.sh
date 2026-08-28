#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python}
WORKERS=${WORKERS:-8}
FORMAL_ROOT=${FORMAL_ROOT:?FORMAL_ROOT is required}
INDEPENDENT_ROOT=${INDEPENDENT_ROOT:?INDEPENDENT_ROOT is required}
OUTPUT_ROOT=${OUTPUT_ROOT:-results/additional_unseen/drtp_utr_2301_2405}

cd "$ROOT_DIR"
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
if [ -e "$OUTPUT_ROOT" ]; then
  test -f "$OUTPUT_ROOT/additional_unseen_tape_manifest.json" || {
    echo "refusing existing non-tape output: $OUTPUT_ROOT" >&2; exit 1;
  }
else
  "$PYTHON_BIN" scripts/create_drtp_additional_unseen_tape.py --output-root "$OUTPUT_ROOT" --execute
fi

"$PYTHON_BIN" scripts/run_drtp_additional_unseen_evaluation.py \
  --formal-root "$FORMAL_ROOT" --independent-root "$INDEPENDENT_ROOT" \
  --output-root "$OUTPUT_ROOT" --workers "$WORKERS" --gpu-ids "${GPU_IDS:-0}" --execute
"$PYTHON_BIN" scripts/aggregate_drtp_additional_unseen_evaluation.py --output-root "$OUTPUT_ROOT" --execute
