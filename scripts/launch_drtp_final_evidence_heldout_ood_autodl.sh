#!/usr/bin/env bash
set -euo pipefail

: "${ARCHIVE_A:?ARCHIVE_A is required}"
: "${ARCHIVE_B:?ARCHIVE_B is required}"
: "${OUTPUT_ROOT:?OUTPUT_ROOT is required}"
: "${WORKERS:=20}"
: "${PYTHON_BIN:=python}"

EVALUATION_ROOT="$OUTPUT_ROOT/evaluations/final_heldout_ood"
REPORT_ROOT="$OUTPUT_ROOT/diagnostics/final_heldout_ood"

test ! -e "$EVALUATION_ROOT" || { echo "Evaluation output exists: $EVALUATION_ROOT" >&2; exit 1; }
test ! -e "$REPORT_ROOT" || { echo "Report output exists: $REPORT_ROOT" >&2; exit 1; }

"$PYTHON_BIN" scripts/run_drtp_final_evidence_heldout_ood_evaluation.py \
  --archive-a "$ARCHIVE_A" --archive-b "$ARCHIVE_B" \
  --output-root "$EVALUATION_ROOT" --workers "$WORKERS" --execute

"$PYTHON_BIN" scripts/aggregate_drtp_final_evidence_heldout_ood.py \
  --evaluation-root "$EVALUATION_ROOT" --output-root "$REPORT_ROOT" --execute

printf '%s\n' '{"status":"DRTP_FINAL_EVIDENCE_HELDOUT_OOD_COMPLETE","training_started":false,"automatic_algorithm_revision":false}' \
  > "$OUTPUT_ROOT/DRTP_FINAL_EVIDENCE_HELDOUT_OOD_COMPLETE.json"
