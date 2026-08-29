#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-${ROOT}/results/development/drtp_stabilization_s1}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
PYTHON_BIN="${PYTHON_BIN:-python}"
[[ "$MAX_PARALLEL" == "6" ]] || { echo "S1 frozen maximum safe concurrency is exactly 6" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }
[[ -f "$ROOT/configs/drtp_stabilization_s0_freeze.json" && -f "$ROOT/configs/drtp_stabilization_s1_development_tape.json" ]] || { echo "missing frozen S0/S1 inputs" >&2; exit 2; }
available_kb=$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')
[[ "$available_kb" -ge 20971520 ]] || { echo "need at least 20 GiB free" >&2; exit 2; }
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"; mkdir -p "$OUT/launcher_logs"
export ROOT OUT PYTHON_BIN
printf '%s\n' \
  'utr_sg 2901' 'utr_sg 2902' 'utr_sg 2903' \
  'drtp_sg 2901' 'drtp_sg 2902' 'drtp_sg 2903' \
  'drtp_tr_sg 2901' 'drtp_tr_sg 2902' 'drtp_tr_sg 2903' |
  xargs -r -n 2 -P "$MAX_PARALLEL" bash -c '
    arm="$1"; seed="$2"
    "$PYTHON_BIN" "$ROOT/scripts/run_drtp_stabilization_s1_single.py" --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
      >"$OUT/launcher_logs/${arm}_seed${seed}.out" 2>"$OUT/launcher_logs/${arm}_seed${seed}.err"
  ' _ || { echo "S1 training failed; evaluation and gate were not started" >&2; exit 3; }
"$PYTHON_BIN" scripts/run_drtp_stabilization_s1_evaluation.py --output-root "$OUT" --workers 6 --execute
"$PYTHON_BIN" scripts/aggregate_drtp_stabilization_s1_05m.py --output-root "$OUT" --execute
echo "S1 gate completed; launcher intentionally stops before S2 or any continuation."
