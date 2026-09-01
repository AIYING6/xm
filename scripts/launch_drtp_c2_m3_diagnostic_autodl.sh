#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_c2_m3_diagnostic}"; MAX_PARALLEL="${MAX_PARALLEL:-15}"; PYTHON_BIN="${PYTHON_BIN:-python}"
[[ ! -e "$OUT" ]] || { echo "refusing existing output" >&2; exit 2; }; mkdir -p "$OUT/launcher_logs"; export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OUT PYTHON_BIN; cd "$ROOT"
printf '%s\n' $(for a in utr_sg group_weighted_utr_sg; do for s in {5101..5110}; do echo "$a:$s"; done; done) | xargs -n1 -P "$MAX_PARALLEL" bash -c 'i="$1"; "$PYTHON_BIN" scripts/run_drtp_c2_m3_diagnostic.py --arm "${i%%:*}" --seed "${i##*:}" --output-root "$OUT" --execute >"$OUT/launcher_logs/${i%%:*}_${i##*:}.out" 2>"$OUT/launcher_logs/${i%%:*}_${i##*:}.err"' _
tar -czf "$ROOT/drtp_c2_m3_diagnostic_training_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"; sha256sum "$ROOT/drtp_c2_m3_diagnostic_training_results.tar.gz" > "$ROOT/drtp_c2_m3_diagnostic_training_results.tar.gz.sha256"
