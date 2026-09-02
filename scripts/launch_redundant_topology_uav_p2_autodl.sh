#!/usr/bin/env bash
# Frozen P2 launcher.  Run only on the cloud; no automatic continuation to P3.
set -euo pipefail
OUT="${OUTPUT_ROOT:-results/development/redundant_topology_uav_p2}"
PARALLEL="${MAX_PARALLEL:-3}"
PY="${PYTHON_BIN:-python}"
mkdir -p "$OUT/launcher_logs"

"$PY" scripts/run_redundant_topology_uav_p2.py q0 --output-root "$OUT" --execute
"$PY" scripts/run_redundant_topology_uav_p2.py random --output-root "$OUT" --execute

run_one() {
  local arm="$1" seed="$2"
  "$PY" scripts/run_redundant_topology_uav_p2.py train --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
    > "$OUT/launcher_logs/${arm}_seed${seed}.out" 2> "$OUT/launcher_logs/${arm}_seed${seed}.err"
}
export -f run_one
export PY OUT
for arm in plain_sg_mappo utr_sg_mappo; do
  for seed in 6201 6202 6203; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    run_one "$arm" "$seed" &
  done
done
wait
for arm in plain_sg_mappo utr_sg_mappo; do
  for seed in 6201 6202 6203; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    "$PY" scripts/run_redundant_topology_uav_p2.py evaluate --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
      > "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.out" 2> "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.err" &
  done
done
wait
"$PY" scripts/run_redundant_topology_uav_p2.py aggregate --output-root "$OUT" --execute
echo '{"status":"P2_TRAINING_COMPLETE","automatic_continuation":false}'
