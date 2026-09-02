#!/usr/bin/env bash
# Frozen P2-R cloud launcher. No automatic P3 continuation.
set -euo pipefail
OUT="${OUTPUT_ROOT:-results/development/redundant_topology_uav_p2r}"
PARALLEL="${MAX_PARALLEL:-5}"
PY="${PYTHON_BIN:-python}"
mkdir -p "$OUT/launcher_logs"

"$PY" scripts/verify_redundant_topology_uav_p2r_preflight.py --output-root "$OUT/preflight" --execute
"$PY" scripts/run_redundant_topology_uav_p2r.py q0 --output-root "$OUT" --execute

run_one() {
  local arm="$1" seed="$2"
  "$PY" scripts/run_redundant_topology_uav_p2r.py train --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
    > "$OUT/launcher_logs/${arm}_seed${seed}.out" 2> "$OUT/launcher_logs/${arm}_seed${seed}.err"
}
export -f run_one
export PY OUT
for arm in plain_role_sg_mappo utr_role_sg_mappo; do
  for seed in 65011 65012 65013 65014 65015; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    run_one "$arm" "$seed" &
  done
done
wait

for arm in plain_role_sg_mappo utr_role_sg_mappo; do
  for seed in 65011 65012 65013 65014 65015; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    "$PY" scripts/run_redundant_topology_uav_p2r.py evaluate --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
      > "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.out" 2> "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.err" &
  done
done
wait
"$PY" scripts/run_redundant_topology_uav_p2r.py aggregate --output-root "$OUT" --execute
echo '{"status":"P2_R_COMPLETE","automatic_continuation":false}'
