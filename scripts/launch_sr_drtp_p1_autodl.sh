#!/usr/bin/env bash
set -euo pipefail
: "${OUTPUT_ROOT:?OUTPUT_ROOT required}"
: "${MAX_PARALLEL:=9}"
: "${PYTHON_BIN:=python}"
mkdir -p "$OUTPUT_ROOT/launcher_logs"
mapfile -t SEEDS < <("$PYTHON_BIN" - <<'PY'
import json
f=json.load(open('configs/sr_drtp_p1_shadow_preparation_freeze.json'))
print(*f['cohorts']['A'],*f['cohorts']['B'],sep='\n')
PY
)
run(){ "$@"; }
export -f run
printf '%s\n' "SR-DRTP P1: official Original-DRTP trajectories=10; max_parallel=$MAX_PARALLEL"
printf '%s\n' "${SEEDS[@]}" | xargs -r -P "$MAX_PARALLEL" -I{} bash -lc 'run "$0" scripts/run_sr_drtp_p1.py official --seed "$1" --output-root "$2" --execute > "$2/launcher_logs/official_seed$1.out" 2> "$2/launcher_logs/official_seed$1.err"' "$PYTHON_BIN" {} "$OUTPUT_ROOT"
for seed in "${SEEDS[@]}"; do for update in 256 512 768 1024 1280 1536 1792; do for branch in A B C; do echo "$seed $update $branch"; done; done; done | xargs -r -n3 -P "$MAX_PARALLEL" bash -lc 'run "$1" scripts/run_sr_drtp_p1.py shadow --seed "$3" --source-update "$4" --branch "$5" --output-root "$2" --execute > "$2/launcher_logs/shadow_seed${3}_u${4}_${5}.out" 2> "$2/launcher_logs/shadow_seed${3}_u${4}_${5}.err"' _ "$PYTHON_BIN" "$OUTPUT_ROOT"
"$PYTHON_BIN" scripts/aggregate_sr_drtp_p1.py --output-root "$OUTPUT_ROOT" --execute
