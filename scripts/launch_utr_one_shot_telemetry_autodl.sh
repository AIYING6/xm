#!/usr/bin/env bash
set -euo pipefail

# This launcher performs diagnostic inference only.  It never calls a trainer.
PYTHON_BIN="${PYTHON_BIN:-python}"
PHASE_D_ROOT="${PHASE_D_ROOT:?Set PHASE_D_ROOT to extracted results/development/phase_d/phase_d_2m}"
DIAGNOSTIC_ROOT="${DIAGNOSTIC_ROOT:-artifacts/diagnostics/utr_mechanism_v2}"
DOCS_ROOT="${DOCS_ROOT:-docs}"

"$PYTHON_BIN" scripts/run_utr_one_shot_telemetry.py \
  --phase-d-root "$PHASE_D_ROOT" \
  --output-root "$DIAGNOSTIC_ROOT" \
  --docs-root "$DOCS_ROOT" \
  --execute

"$PYTHON_BIN" scripts/analyze_utr_good_weak_mechanism_v2.py \
  --input-root "$DIAGNOSTIC_ROOT" \
  --docs-root "$DOCS_ROOT" \
  --execute
