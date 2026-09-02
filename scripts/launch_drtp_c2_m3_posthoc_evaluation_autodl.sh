#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_c2_m3_diagnostic}"
WORKERS="${WORKERS:-15}"
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" scripts/run_drtp_c2_m3_posthoc_evaluation.py --output-root "$OUT" --workers "$WORKERS" --execute
"$PYTHON_BIN" scripts/aggregate_drtp_c2_m3_posthoc_evaluation.py --output-root "$OUT" --execute
tar -czf "$ROOT/drtp_c2_m3_posthoc_evaluation_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/drtp_c2_m3_posthoc_evaluation_results.tar.gz" > "$ROOT/drtp_c2_m3_posthoc_evaluation_results.tar.gz.sha256"
