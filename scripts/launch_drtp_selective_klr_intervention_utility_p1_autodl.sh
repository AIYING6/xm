#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_selective_klr_intervention_utility_p1}"
MAX_PARALLEL="${MAX_PARALLEL:-9}"; PYTHON_BIN="${PYTHON_BIN:-python}"
[[ "$MAX_PARALLEL" == "9" ]] || { echo "P1 requires frozen MAX_PARALLEL=9" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }
[[ $(df -Pk "$ROOT" | awk 'NR==2{print $4}') -ge 20971520 ]] || { echo "need 20GiB free" >&2; exit 2; }
export PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p "$OUT/launcher_logs" "$OUT/diagnostics/preflight"; cd "$ROOT"
"$PYTHON_BIN" scripts/verify_drtp_selective_klr_intervention_utility_p1_preflight.py --output "$OUT/diagnostics/preflight/P1_PREFLIGHT.json"
printf '%s\n' {3801..3810} | xargs -n1 -P "$MAX_PARALLEL" bash -c 's="$1"; "$PYTHON_BIN" "$ROOT/scripts/run_drtp_selective_klr_intervention_utility_p1_single.py" --seed "$s" --output-root "$OUT" --execute >"$OUT/launcher_logs/drtp_sg_seed${s}.out" 2>"$OUT/launcher_logs/drtp_sg_seed${s}.err"' _ || { echo "P1 training failed; aggregate not started" >&2; exit 3; }
"$PYTHON_BIN" scripts/aggregate_drtp_selective_klr_intervention_utility_p1.py --output-root "$OUT" --execute
tar -czf "$ROOT/drtp_selective_klr_intervention_utility_p1_05m_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/drtp_selective_klr_intervention_utility_p1_05m_results.tar.gz" > "$ROOT/drtp_selective_klr_intervention_utility_p1_05m_results.tar.gz.sha256"
echo "P1 complete; Selective-KLR remains unauthorized."
