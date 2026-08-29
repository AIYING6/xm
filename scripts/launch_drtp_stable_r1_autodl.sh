#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_stable_r1}"
MAX_PARALLEL="${MAX_PARALLEL:-15}"
PYTHON_BIN="${PYTHON_BIN:-python}"
[[ "$MAX_PARALLEL" == "15" ]] || { echo "R1 authorization freezes all-15 parallel launch" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }
available_kb=$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')
[[ "$available_kb" -ge 26214400 ]] || { echo "need at least 25 GiB free" >&2; exit 2; }
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"; mkdir -p "$OUT/launcher_logs" "$OUT/diagnostics/stable_r1/technical"
"$PYTHON_BIN" scripts/run_drtp_stable_r1_technical_audit.py --output "$OUT/diagnostics/stable_r1/technical/R1_TECHNICAL_AUDIT.json" --execute
export ROOT OUT PYTHON_BIN
printf '%s\n' utr_sg:3001 utr_sg:3002 utr_sg:3003 utr_sg:3004 utr_sg:3005 drtp_sg:3001 drtp_sg:3002 drtp_sg:3003 drtp_sg:3004 drtp_sg:3005 conservative_drtp_sg:3001 conservative_drtp_sg:3002 conservative_drtp_sg:3003 conservative_drtp_sg:3004 conservative_drtp_sg:3005 | xargs -r -n 1 -P "$MAX_PARALLEL" bash -c '
  spec="$1"; arm="${spec%%:*}"; seed="${spec##*:}"
  "$PYTHON_BIN" "$ROOT/scripts/run_drtp_stable_r1_single.py" --arm "$arm" --seed "$seed" --output-root "$OUT" --execute >"$OUT/launcher_logs/${arm}_seed${seed}.out" 2>"$OUT/launcher_logs/${arm}_seed${seed}.err"
' _ || { echo "R1 training failed; evaluation not started" >&2; exit 3; }
"$PYTHON_BIN" scripts/run_drtp_stable_r1_evaluation.py --output-root "$OUT" --workers 8 --execute
"$PYTHON_BIN" scripts/aggregate_drtp_stable_r1.py --output-root "$OUT" --technical-audit "$OUT/diagnostics/stable_r1/technical/R1_TECHNICAL_AUDIT.json" --execute
tar -czf "$ROOT/drtp_stable_r1_1m_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/drtp_stable_r1_1m_results.tar.gz" > "$ROOT/drtp_stable_r1_1m_results.tar.gz.sha256"
cp "$ROOT/drtp_stable_r1_1m_results.tar.gz.sha256" "$OUT/diagnostics/stable_r1/gate/R1_RESULT_ARCHIVE_SHA256.txt"
echo "R1 complete; no 3M continuation or 10M confirmation was started."
