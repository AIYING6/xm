#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_klr_final_replication_p3}"; MAX_PARALLEL="${MAX_PARALLEL:-9}"; PYTHON_BIN="${PYTHON_BIN:-python}"
[[ "$MAX_PARALLEL" == "9" ]] || { echo "Frozen P3 requires MAX_PARALLEL=9" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }; [[ $(df -Pk "$ROOT"|awk 'NR==2{print $4}') -ge 15728640 ]] || { echo "need 15GiB free" >&2; exit 2; }
export PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p "$OUT/launcher_logs" "$OUT/diagnostics/preflight"; cd "$ROOT"
"$PYTHON_BIN" scripts/verify_drtp_klr_final_replication_p3_preflight.py --output "$OUT/diagnostics/preflight/P3_PREFLIGHT.json"
printf '%s\n' $(for a in utr_sg drtp_sg drtp_klr_sg; do for s in {3701..3710}; do echo "$a:$s"; done; done) | xargs -n1 -P "$MAX_PARALLEL" bash -c 'z="$1"; a="${z%%:*}"; s="${z##*:}"; "$PYTHON_BIN" "$ROOT/scripts/run_drtp_klr_final_replication_single.py" --arm "$a" --seed "$s" --output-root "$OUT" --execute >"$OUT/launcher_logs/${a}_seed${s}.out" 2>"$OUT/launcher_logs/${a}_seed${s}.err"' _ || { echo "training failed: evaluation not started" >&2; exit 3; }
"$PYTHON_BIN" scripts/run_drtp_klr_final_replication_p3_evaluation.py --output-root "$OUT" --workers 9 --execute
"$PYTHON_BIN" scripts/aggregate_drtp_klr_final_replication_p3.py --output-root "$OUT" --execute
tar -czf "$ROOT/drtp_klr_final_replication_p3_05m_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/drtp_klr_final_replication_p3_05m_results.tar.gz" > "$ROOT/drtp_klr_final_replication_p3_05m_results.tar.gz.sha256"
echo "P3 complete; no continuation, tuning, or new KLR variant was started."
