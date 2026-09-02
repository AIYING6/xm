#!/usr/bin/env bash
set -euo pipefail
OUT="${OUTPUT_ROOT:-results/development/redundant_topology_uav_p2_9}"
PARALLEL="${MAX_PARALLEL:-6}"
PY="${PYTHON_BIN:-python}"
mkdir -p "$OUT/launcher_logs"

"$PY" scripts/verify_redundant_topology_uav_p2_9_preflight.py --output-root "$OUT/preflight" --execute
"$PY" scripts/run_redundant_topology_uav_p2_9.py q0 --output-root "$OUT" --execute

run_one() { "$PY" scripts/run_redundant_topology_uav_p2_9.py train --arm "$1" --seed "$2" --output-root "$OUT" --execute > "$OUT/launcher_logs/${1}_seed${2}.out" 2> "$OUT/launcher_logs/${1}_seed${2}.err"; }
export -f run_one; export PY OUT
for arm in plain_assigned_role_sg_mappo utr_assigned_role_sg_mappo; do
  for seed in 66011 66012 66013 66014 66015; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    run_one "$arm" "$seed" &
  done
done
wait
for arm in plain_assigned_role_sg_mappo utr_assigned_role_sg_mappo; do
  for seed in 66011 66012 66013 66014 66015; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    "$PY" scripts/run_redundant_topology_uav_p2_9.py evaluate --arm "$arm" --seed "$seed" --output-root "$OUT" --execute > "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.out" 2> "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.err" &
  done
done
wait
"$PY" scripts/run_redundant_topology_uav_p2_9.py aggregate --output-root "$OUT" --execute
echo '{"status":"P2_9_COMPLETE","automatic_continuation":false}'
