#!/usr/bin/env bash
set -euo pipefail

: "${OUTPUT_ROOT:?OUTPUT_ROOT is required}"
PYTHON_BIN="${PYTHON_BIN:-python}"
MAX_PARALLEL="${MAX_PARALLEL:-3}"
if [[ "$MAX_PARALLEL" -lt 1 || "$MAX_PARALLEL" -gt 3 ]]; then
  echo "MAX_PARALLEL must be in [1,3] for the three frozen UTR pilot seeds" >&2
  exit 2
fi

"$PYTHON_BIN" scripts/verify_drtp_6uav_v3_utr_pilot_preflight.py --output-root "$OUTPUT_ROOT/preflight" --execute

run_phase() {
  local mode="$1"
  local active=0
  for seed in 94011 94012 94013; do
    "$PYTHON_BIN" scripts/run_drtp_6uav_v3_utr_pilot.py "$mode" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute &
    active=$((active + 1))
    if [[ "$active" -ge "$MAX_PARALLEL" ]]; then
      wait -n
      active=$((active - 1))
    fi
  done
  wait
}

run_phase train
run_phase evaluate
"$PYTHON_BIN" scripts/run_drtp_6uav_v3_utr_pilot.py aggregate --output-root "$OUTPUT_ROOT" --execute
