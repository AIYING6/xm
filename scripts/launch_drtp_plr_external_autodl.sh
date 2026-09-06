#!/usr/bin/env bash
# Frozen 3-UAV external comparator: UTR, Original DRTP, and group-level PLR.
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/final_evidence/drtp_plr_external_formal}"
MAX_PARALLEL="${MAX_PARALLEL:-15}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-20}"
[[ "$MAX_PARALLEL" =~ ^[0-9]+$ && "$MAX_PARALLEL" -ge 1 && "$MAX_PARALLEL" -le 20 ]] || { echo "MAX_PARALLEL must be 1..20" >&2; exit 2; }
[[ ! -e "$OUTPUT_ROOT/runs" ]] || { echo "refusing to overwrite formal runs: $OUTPUT_ROOT/runs" >&2; exit 2; }
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(( CPU_THREADS_TOTAL / MAX_PARALLEL ))}"; [[ "$OMP_NUM_THREADS" -ge 1 ]] || export OMP_NUM_THREADS=1
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}" OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-$OMP_NUM_THREADS}" NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-$OMP_NUM_THREADS}"
mkdir -p "$OUTPUT_ROOT/launcher_logs"
"$PYTHON_BIN" scripts/verify_drtp_plr_and_6uav_formal_preflight.py --output-root "$OUTPUT_ROOT/preflight" --execute
"$PYTHON_BIN" scripts/create_drtp_plr_external_tape.py --output-root "$OUTPUT_ROOT/tape"

train_one() { "$PYTHON_BIN" scripts/run_drtp_plr_external_single.py --arm "$1" --seed "$2" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/launcher_logs/train_${1}_seed${2}.out" 2> "$OUTPUT_ROOT/launcher_logs/train_${1}_seed${2}.err"; }
for arm in utr_sg drtp_sg plr_style_sg; do for seed in 79011 79012 79013 79014 79015; do while [[ "$(jobs -rp | wc -l)" -ge "$MAX_PARALLEL" ]]; do wait -n; done; train_one "$arm" "$seed" & done; done
wait
printf '{"status":"DRTP_PLR_EXTERNAL_TRAINING_COMPLETE","trajectories":15,"evaluation_started":false,"automatic_algorithm_revision":false}\n' > "$OUTPUT_ROOT/DRTP_PLR_EXTERNAL_TRAINING_COMPLETE.json"
"$PYTHON_BIN" scripts/run_drtp_plr_external_evaluation.py --trained-root "$OUTPUT_ROOT" --output-root "$OUTPUT_ROOT/evaluations/final_10m" --workers "$MAX_PARALLEL" --execute
"$PYTHON_BIN" scripts/aggregate_drtp_plr_external.py --evaluation-root "$OUTPUT_ROOT/evaluations/final_10m" --output-root "$OUTPUT_ROOT" --execute
printf '{"status":"DRTP_PLR_EXTERNAL_COMPLETE","trajectories":15,"endpoint_evaluation_completed":true,"automatic_algorithm_revision":false,"automatic_continuation":false}\n' > "$OUTPUT_ROOT/DRTP_PLR_EXTERNAL_COMPLETE.json"
echo "PLR external comparator complete; no automatic algorithm revision was started."
