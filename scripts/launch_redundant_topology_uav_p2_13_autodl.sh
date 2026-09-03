#!/usr/bin/env bash
set -euo pipefail
OUT="${OUTPUT_ROOT:-results/development/redundant_topology_uav_p2_13}"
PARALLEL="${MAX_PARALLEL:-6}"
PY="${PYTHON_BIN:-python}"
mkdir -p "$OUT/launcher_logs"

test -f "$OUT/preflight/diagnostics/P2_13_PREFLIGHT.json"
grep -q '"verdict": "P2_13_PREFLIGHT_PASS"' "$OUT/preflight/diagnostics/P2_13_PREFLIGHT.json"
"$PY" scripts/run_redundant_topology_uav_p2_13.py q0 --output-root "$OUT" --execute

run_one() {
  "$PY" scripts/run_redundant_topology_uav_p2_13.py train --arm "$1" --seed "$2" --output-root "$OUT" --execute > "$OUT/launcher_logs/${1}_seed${2}.out" 2> "$OUT/launcher_logs/${1}_seed${2}.err"
}
for arm in plain_scout_terminal_assigned_role_sg_mappo utr_scout_terminal_assigned_role_sg_mappo; do
  for seed in 67011 67012 67013 67014 67015; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    run_one "$arm" "$seed" &
  done
done
wait
for arm in plain_scout_terminal_assigned_role_sg_mappo utr_scout_terminal_assigned_role_sg_mappo; do
  for seed in 67011 67012 67013 67014 67015; do
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLEL" ]; do wait -n; done
    "$PY" scripts/run_redundant_topology_uav_p2_13.py evaluate --arm "$arm" --seed "$seed" --output-root "$OUT" --execute > "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.out" 2> "$OUT/launcher_logs/evaluate_${arm}_seed${seed}.err" &
  done
done
wait
"$PY" scripts/run_redundant_topology_uav_p2_13.py aggregate --output-root "$OUT" --execute
echo '{"status":"P2_13_COMPLETE","automatic_continuation":false}'
