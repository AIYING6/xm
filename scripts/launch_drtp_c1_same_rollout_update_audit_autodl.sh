#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_c1_same_rollout_update_audit}"
SOURCE_ROOT="${SOURCE_ROOT:?SOURCE_ROOT must point to extracted frozen UTR seed assets}"
MAX_PARALLEL="${MAX_PARALLEL:-5}"
PYTHON_BIN="${PYTHON_BIN:-python}"

[[ "$MAX_PARALLEL" =~ ^[1-9][0-9]*$ && "$MAX_PARALLEL" -le 20 ]] || {
  echo "MAX_PARALLEL must be 1..20" >&2; exit 2;
}
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }
[[ -d "$SOURCE_ROOT" ]] || { echo "missing C1 source assets: $SOURCE_ROOT" >&2; exit 2; }

export PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p "$OUT/launcher_logs" "$OUT/diagnostics/preflight"
cd "$ROOT"
export ROOT OUT SOURCE_ROOT PYTHON_BIN

"$PYTHON_BIN" scripts/verify_drtp_c1_same_rollout_update_audit_preflight.py \
  --source-root "$SOURCE_ROOT" \
  --output "$OUT/diagnostics/preflight/C1_PREFLIGHT.json"

printf '%s\n' 2201 2202 2203 2204 2205 | xargs -n1 -P "$MAX_PARALLEL" bash -c '
  seed="$1"
  "$PYTHON_BIN" "$ROOT/scripts/run_drtp_c1_same_rollout_update_audit.py" \
    --seed "$seed" --source-root "$SOURCE_ROOT" --output-root "$OUT" --execute \
    >"$OUT/launcher_logs/seed${seed}.out" \
    2>"$OUT/launcher_logs/seed${seed}.err"
' _

"$PYTHON_BIN" scripts/aggregate_drtp_c1_same_rollout_update_audit.py \
  --output-root "$OUT" --execute

tar -czf "$ROOT/drtp_c1_same_rollout_update_audit_results.tar.gz" \
  -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/drtp_c1_same_rollout_update_audit_results.tar.gz" \
  > "$ROOT/drtp_c1_same_rollout_update_audit_results.tar.gz.sha256"
echo "C1 complete; no C2 pilot, formal evaluation, or longer training started."
