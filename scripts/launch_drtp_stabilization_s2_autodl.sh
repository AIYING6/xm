#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-${ROOT}/results/development/drtp_stabilization_s2}"
S1_ROOT="${S1_ROOT:?S1_ROOT must point to extracted frozen S1 results}"
RESULT_ARCHIVE="${RESULT_ARCHIVE:-${ROOT}/drtp_stabilization_s2_05m_results.tar.gz}"
MAX_PARALLEL="${MAX_PARALLEL:-3}"
PYTHON_BIN="${PYTHON_BIN:-python}"
[[ "$MAX_PARALLEL" == "3" ]] || { echo "S2 maximum safe concurrency is exactly 3" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing S2 output root: $OUT" >&2; exit 2; }
[[ -d "$S1_ROOT" ]] || { echo "missing extracted S1 baseline root: $S1_ROOT" >&2; exit 2; }
[[ ! -e "$RESULT_ARCHIVE" && ! -e "${RESULT_ARCHIVE}.sha256" ]] || { echo "refusing existing result archive" >&2; exit 2; }
available_kb=$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')
[[ "$available_kb" -ge 20971520 ]] || { echo "need at least 20 GiB free" >&2; exit 2; }
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"; mkdir -p "$OUT/launcher_logs" "$OUT/diagnostics/s2_05m_gate"
"$PYTHON_BIN" scripts/run_drtp_stabilization_s2_technical_audit.py --output-dir "$OUT/diagnostics/s2_05m_gate/technical_audit" --execute
cp "$OUT/diagnostics/s2_05m_gate/technical_audit/S2_TECHNICAL_AUDIT.json" "$OUT/diagnostics/s2_05m_gate/S2_TECHNICAL_AUDIT.json"
export ROOT OUT S1_ROOT PYTHON_BIN
printf '%s\n' 2901 2902 2903 | xargs -r -n 1 -P "$MAX_PARALLEL" bash -c '
  seed="$1"
  "$PYTHON_BIN" "$ROOT/scripts/run_drtp_stabilization_s2_single.py" --seed "$seed" --output-root "$OUT" --s1-root "$S1_ROOT" --execute \
    >"$OUT/launcher_logs/conservative_drtp_sg_seed${seed}.out" 2>"$OUT/launcher_logs/conservative_drtp_sg_seed${seed}.err"
' _ || { echo "S2 training failed; evaluation and gate were not started" >&2; exit 3; }
"$PYTHON_BIN" scripts/run_drtp_stabilization_s2_evaluation.py --output-root "$OUT" --s1-root "$S1_ROOT" --workers 3 --execute
"$PYTHON_BIN" scripts/aggregate_drtp_stabilization_s2_05m.py --output-root "$OUT" --s1-root "$S1_ROOT" --technical-audit "$OUT/diagnostics/s2_05m_gate/S2_TECHNICAL_AUDIT.json" --execute
tar -czf "$RESULT_ARCHIVE" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$RESULT_ARCHIVE" > "${RESULT_ARCHIVE}.sha256"
cp "${RESULT_ARCHIVE}.sha256" "$OUT/diagnostics/s2_05m_gate/S2_RESULT_ARCHIVE_SHA256.txt"
echo "S2 gate completed; launcher intentionally stops before any continuation or third candidate."
