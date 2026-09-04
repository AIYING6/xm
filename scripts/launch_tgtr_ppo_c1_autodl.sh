#!/usr/bin/env bash
set -euo pipefail

OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/tgtr_ppo_c1}"
SOURCE_ROOT="${SOURCE_ROOT:-results/development/t1_telemetry_native_reference_1m_run1/runs/utr_sg}"
MAX_PARALLEL="${MAX_PARALLEL:-5}"
PYTHON_BIN="${PYTHON_BIN:-python}"

mkdir -p "$OUTPUT_ROOT/diagnostics"
"$PYTHON_BIN" scripts/verify_tgtr_ppo_c1_preflight.py \
  --source-root "$SOURCE_ROOT" \
  --output "$OUTPUT_ROOT/diagnostics/TGTR_C1_PREFLIGHT.json"

run_one() {
  local seed="$1"
  "$PYTHON_BIN" scripts/run_tgtr_ppo_c1_same_rollout.py \
    --seed "$seed" --source-root "$SOURCE_ROOT" --output-root "$OUTPUT_ROOT" --execute \
    > "$OUTPUT_ROOT/tgtr_c1_seed${seed}.out" 2> "$OUTPUT_ROOT/tgtr_c1_seed${seed}.err"
}

for seed in 2201 2202 2203 2204 2205; do
  while [ "$(jobs -rp | wc -l)" -ge "$MAX_PARALLEL" ]; do wait -n; done
  run_one "$seed" &
done
wait

"$PYTHON_BIN" scripts/aggregate_tgtr_ppo_c1.py --output-root "$OUTPUT_ROOT" --execute
