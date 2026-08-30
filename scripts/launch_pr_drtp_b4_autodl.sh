#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSET_ROOT="${ASSET_ROOT:-$ROOT/pr_drtp_b4_assets}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$ROOT/results/feasibility/pr_drtp_b4}"
PYTHON_BIN="${PYTHON_BIN:-python}"
WORKERS="${WORKERS:-20}"

[[ "$WORKERS" =~ ^[0-9]+$ ]] && [[ "$WORKERS" -ge 1 ]] && [[ "$WORKERS" -le 20 ]] || {
  echo 'WORKERS must be an integer from 1 to 20' >&2
  exit 2
}
[[ -f "$ASSET_ROOT/ASSET_MANIFEST.json" ]] || {
  echo "missing PR-DRTP B4 assets: $ASSET_ROOT" >&2
  exit 2
}
[[ ! -e "$OUTPUT_ROOT" ]] || {
  echo "refusing existing output: $OUTPUT_ROOT" >&2
  exit 2
}
[[ "$(df -Pk "$ROOT" | awk 'NR==2{print $4}')" -ge 5242880 ]] || {
  echo 'need at least 5 GiB free' >&2
  exit 2
}

export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
cd "$ROOT"

"$PYTHON_BIN" scripts/verify_pr_drtp_b4_preflight.py \
  --asset-root "$ASSET_ROOT" \
  --output "$ROOT/PR_DRTP_B4_PREFLIGHT.json"

"$PYTHON_BIN" scripts/run_pr_drtp_b4_evaluation.py \
  --asset-root "$ASSET_ROOT" \
  --output-root "$OUTPUT_ROOT" \
  --workers "$WORKERS" \
  --execute

"$PYTHON_BIN" scripts/aggregate_pr_drtp_b4.py \
  --asset-root "$ASSET_ROOT" \
  --output-root "$OUTPUT_ROOT" \
  --execute

ARCHIVE="$ROOT/pr_drtp_b4_zero_training_feasibility_results.tar.gz"
[[ ! -e "$ARCHIVE" ]] || {
  echo "refusing existing result archive: $ARCHIVE" >&2
  exit 2
}
tar -czf "$ARCHIVE" -C "$(dirname "$OUTPUT_ROOT")" "$(basename "$OUTPUT_ROOT")"
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
echo 'PR-DRTP B4 zero-training feasibility complete; no training was started.'
