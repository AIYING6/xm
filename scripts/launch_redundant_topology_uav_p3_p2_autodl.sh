#!/usr/bin/env bash
set -euo pipefail
OUT="${OUTPUT_ROOT:-results/development/redundant_topology_uav_p3_p2}"
PARALLEL="${MAX_PARALLEL:-10}"
PY="${PYTHON_BIN:-python}"
mkdir -p "$OUT/launcher_logs"

"$PY" scripts/run_redundant_topology_uav_p3_p2.py q0 --output-root "$OUT" --execute
run_one() {
  "$PY" scripts/run_redundant_topology_uav_p3_p2.py train --arm "$1" --seed "$2" --output-root "$OUT" --execute > "$OUT/launcher_logs/${1}_seed${2}.out" 2> "$OUT/launcher_logs/${1}_seed${2}.err"
}
for arm in utr_scout_terminal_assigned_role_sg_mappo staged_topology_scout_terminal_assigned_role_sg_mappo; do
  for seed in 68011 68012 68013 68014 68015; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    run_one "$arm" "$seed" &
  done
done
wait
for arm in utr_scout_terminal_assigned_role_sg_mappo staged_topology_scout_terminal_assigned_role_sg_mappo; do
  for seed in 68011 68012 68013 68014 68015; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    "$PY" scripts/run_redundant_topology_uav_p3_p2.py evaluate --arm "$arm" --seed "$seed" --output-root "$OUT" --execute > "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.out" 2> "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.err" &
  done
done
wait
"$PY" scripts/run_redundant_topology_uav_p3_p2.py aggregate --output-root "$OUT" --execute
echo '{"status":"P3_P2_COMPLETE","automatic_continuation":false}'
