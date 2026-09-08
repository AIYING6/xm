#!/usr/bin/env bash
set -euo pipefail
: "${OUTPUT_ROOT:?OUTPUT_ROOT is required}"
PYTHON_BIN="${PYTHON_BIN:-python}"; MAX_PARALLEL="${MAX_PARALLEL:-3}"
[[ "$MAX_PARALLEL" -ge 1 && "$MAX_PARALLEL" -le 3 ]] || { echo "MAX_PARALLEL must be in [1,3]" >&2; exit 2; }
"$PYTHON_BIN" scripts/verify_drtp_6uav_v31_utr_pilot_preflight.py --output-root "$OUTPUT_ROOT/preflight" --execute
phase() { local mode="$1" active=0; for seed in 95011 95012 95013; do "$PYTHON_BIN" scripts/run_drtp_6uav_v31_utr_pilot.py "$mode" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute & active=$((active+1)); if [[ "$active" -ge "$MAX_PARALLEL" ]]; then wait -n; active=$((active-1)); fi; done; wait; }
phase train
phase evaluate
"$PYTHON_BIN" scripts/run_drtp_6uav_v31_utr_pilot.py aggregate --output-root "$OUTPUT_ROOT" --execute
