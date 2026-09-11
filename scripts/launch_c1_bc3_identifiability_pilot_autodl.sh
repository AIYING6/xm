#!/usr/bin/env bash
# Frozen short C1 pilot: 4 arms x 3 seeds; no automatic budget extension.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/c1_bc3_identifiability_pilot}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
ARMS=(ff_mappo recurrent_mappo bc3_mappo shuffled_bc3_mappo)
SEEDS=(91111 91112 91113)

if [[ -e "$OUTPUT_ROOT" ]]; then
  echo "Refusing to overwrite existing output root: $OUTPUT_ROOT" >&2
  exit 1
fi
mkdir -p "$OUTPUT_ROOT"

"$PYTHON_BIN" scripts/verify_c1_bc3_identifiability_preflight.py \
  --output "$OUTPUT_ROOT/preflight" --execute

running=0
for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    "$PYTHON_BIN" scripts/run_c1_bc3_identifiability_pilot.py train \
      --arm "$arm" --seed "$seed" \
      --output "$OUTPUT_ROOT/runs/$arm/seed$seed" --execute &
    running=$((running + 1))
    if (( running >= MAX_PARALLEL )); then
      wait -n
      running=$((running - 1))
    fi
  done
done
wait

for arm in "${ARMS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    "$PYTHON_BIN" scripts/run_c1_bc3_identifiability_pilot.py evaluate \
      --seed "$seed" \
      --checkpoint "$OUTPUT_ROOT/runs/$arm/seed$seed/endpoint.pt" \
      --output "$OUTPUT_ROOT/runs/$arm/seed$seed/evaluation" --execute
  done
done

"$PYTHON_BIN" scripts/aggregate_c1_bc3_identifiability_pilot.py \
  --output-root "$OUTPUT_ROOT" --execute

printf '{"status":"C1_BC3_PILOT_COMPLETE","trajectories":12,"automatic_continuation":false}\n' \
  > "$OUTPUT_ROOT/C1_BC3_PILOT_COMPLETE.json"
