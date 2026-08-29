#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-${ROOT}/results/development/drtp_h2_confirmation_stage1}"
REPORT_DIR="${REPORT_DIR:-${ROOT}/docs/drtp_bline_h2_confirmation}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
PYTHON_BIN="${PYTHON_BIN:-python}"
[[ "$MAX_PARALLEL" == "10" ]] || { echo "H2 confirmation concurrency is frozen at exactly 10" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }
[[ ! -e "$REPORT_DIR/H2_05M_GATE_REPORT.md" ]] || { echo "refusing existing Stage-1 gate" >&2; exit 2; }
[[ -f "$ROOT/configs/drtp_h2_confirmation_development_tape.json" ]] || { echo "missing frozen tape" >&2; exit 2; }
available_kb=$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')
[[ "$available_kb" -ge 26214400 ]] || { echo "need at least 25 GiB free for telemetry/checkpoints" >&2; exit 2; }
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"; mkdir -p "$OUT/launcher_logs"
declare -a pids=(); failed=0
launch() {
  local arm="$1" seed="$2"
  "$PYTHON_BIN" scripts/run_drtp_h2_confirmation_single.py --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
    >"$OUT/launcher_logs/${arm}_seed${seed}.out" 2>"$OUT/launcher_logs/${arm}_seed${seed}.err" &
  pids+=("$!")
}
for arm in utr_sg drtp_sg; do
  for seed in 2801 2802 2803 2804 2805; do
    while [[ $(jobs -pr | wc -l) -ge "$MAX_PARALLEL" ]]; do wait -n || failed=1; done
    launch "$arm" "$seed"
  done
done
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
[[ "$failed" == 0 ]] || { echo "H2 Stage-1 training failure; gate is not started" >&2; exit 3; }
"$PYTHON_BIN" scripts/aggregate_drtp_h2_confirmation_05m.py --output-root "$OUT" --report-dir "$REPORT_DIR" --execute
echo "H2 Stage-1 gate completed; launcher intentionally stops before any 1M continuation."
