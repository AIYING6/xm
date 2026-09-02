#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_c2_m3_diagnostic}"
MAX_PARALLEL="${MAX_PARALLEL:-15}"
PYTHON_BIN="${PYTHON_BIN:-python}"
[[ -d "$OUT/runs" ]] || { echo "missing completed M3 runs: $OUT/runs" >&2; exit 2; }
mkdir -p "$OUT/launcher_logs_1m_extension"
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OUT PYTHON_BIN
cd "$ROOT"
printf '%s\n' $(for arm in utr_sg group_weighted_utr_sg; do for seed in {5101..5110}; do echo "$arm:$seed"; done; done) |
  xargs -n1 -P "$MAX_PARALLEL" bash -c '
    item="$1"; arm="${item%%:*}"; seed="${item##*:}"
    "$PYTHON_BIN" scripts/run_drtp_c2_m3_1m_extension.py --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
      >"$OUT/launcher_logs_1m_extension/${arm}_${seed}.out" \
      2>"$OUT/launcher_logs_1m_extension/${arm}_${seed}.err"
  ' _
tar -czf "$ROOT/drtp_c2_m3_1m_extension_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/drtp_c2_m3_1m_extension_results.tar.gz" > "$ROOT/drtp_c2_m3_1m_extension_results.tar.gz.sha256"
