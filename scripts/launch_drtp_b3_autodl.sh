#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-${ROOT}/results/development/drtp_b3}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
PYTHON_BIN="${PYTHON_BIN:-python}"
[[ "$MAX_PARALLEL" == "6" ]] || { echo "B3 frozen maximum concurrency is exactly 6" >&2; exit 2; }
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"
[[ -f configs/drtp_b3_development_tape.json ]] || { echo "missing tape" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }
mkdir -p "$OUT/launcher_logs"
pids=(); failed=0
for arm in utr_sg drtp_sg; do for seed in 2701 2702 2703; do
  "$PYTHON_BIN" scripts/run_drtp_b3_single.py --arm "$arm" --seed "$seed" --output-root "$OUT" --execute >"$OUT/launcher_logs/${arm}_seed${seed}.out" 2>"$OUT/launcher_logs/${arm}_seed${seed}.err" & pids+=("$!")
done; done
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
[[ "$failed" == 0 ]] || { echo "B3 training failure; no evaluation started" >&2; exit 3; }
"$PYTHON_BIN" scripts/run_drtp_b3_evaluation.py --output-root "$OUT" --workers 6 --execute
"$PYTHON_BIN" scripts/aggregate_drtp_b3_1m.py --output-root "$OUT" --execute
