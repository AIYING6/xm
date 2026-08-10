#!/usr/bin/env bash
# Frozen F2-R2 confirmation only: 24 selected checkpoints x 300 paired episodes.
# It never trains or selects a checkpoint. The caller may shut down the instance
# only after this script exits successfully.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
F1_ROOT="${F1_ROOT:?set frozen F1 formal-output root}"
OUT_ROOT="${OUT_ROOT:-results/v1_9_f2_r2_confirmatory}"
EXPECTED_F1_SOURCE_COMMIT="${EXPECTED_F1_SOURCE_COMMIT:?set full F1 source commit}"
EXPECTED_EVALUATOR_SOURCE_COMMIT="${EXPECTED_EVALUATOR_SOURCE_COMMIT:?set full F2 evaluator source commit}"
export OMP_NUM_THREADS=1

[[ "$(git rev-parse HEAD)" == "$EXPECTED_EVALUATOR_SOURCE_COMMIT" ]] || { echo "F2 evaluator source commit mismatch" >&2; exit 2; }
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || { echo "tracked source tree is dirty" >&2; exit 2; }
[[ -d "$F1_ROOT" ]] || { echo "frozen F1 output root is unavailable: $F1_ROOT" >&2; exit 2; }
[[ ! -e "$OUT_ROOT" ]] || { echo "refusing to reuse F2 output root: $OUT_ROOT" >&2; exit 2; }

"$PYTHON_BIN" - <<'PY'
import torch
if not torch.cuda.is_available() or torch.cuda.get_device_properties(0).total_memory < 16 * 1024**3:
    raise SystemExit("F2-R2 requires CUDA GPU memory >=16 GiB")
print(torch.cuda.get_device_name(0))
PY

# These tests use only synthetic/temp data. No F2 episode is opened before the
# immutable launch preflight below has passed.
"$PYTHON_BIN" scripts/test_v1_9_f2_synthetic_preflight.py
"$PYTHON_BIN" scripts/test_v1_9_f2_r2_static.py
"$PYTHON_BIN" scripts/test_actor_boundary_v1_8.py
"$PYTHON_BIN" scripts/test_pcrf_r2_d0_v1_9.py
"$PYTHON_BIN" scripts/test_p0_a_terminal_estimand_v1_9.py

"$PYTHON_BIN" scripts/prepare_v1_9_f2_r2_preflight.py \
  --f1-root "$F1_ROOT" --out-root "$OUT_ROOT" \
  --expected-f1-source-commit "$EXPECTED_F1_SOURCE_COMMIT" \
  --expected-evaluator-source-commit "$EXPECTED_EVALUATOR_SOURCE_COMMIT"

"$PYTHON_BIN" scripts/evaluate_v1_9_f2_r2.py \
  --f1-root "$F1_ROOT" --out-root "$OUT_ROOT" \
  --expected-f1-source-commit "$EXPECTED_F1_SOURCE_COMMIT" \
  --expected-evaluator-source-commit "$EXPECTED_EVALUATOR_SOURCE_COMMIT" --device cuda

"$PYTHON_BIN" scripts/check_v1_9_f2_r2_artifacts.py \
  --root "$OUT_ROOT" --expected-f1-source-commit "$EXPECTED_F1_SOURCE_COMMIT" \
  --expected-evaluator-source-commit "$EXPECTED_EVALUATOR_SOURCE_COMMIT" \
  --output "$OUT_ROOT/F2_R2_CONFIRMATORY_ARTIFACT_GATE_MANIFEST.json"

"$PYTHON_BIN" scripts/analyze_v1_9_f2_r2.py \
  --root "$OUT_ROOT" --expected-f1-source-commit "$EXPECTED_F1_SOURCE_COMMIT" \
  --expected-evaluator-source-commit "$EXPECTED_EVALUATOR_SOURCE_COMMIT" \
  --output "$OUT_ROOT/F2_R2_CONFIRMATORY_ANALYSIS.json"

echo "F2_R2_CONFIRMATORY_COMPLETE__AUTHOR_REVIEW_REQUIRED"
