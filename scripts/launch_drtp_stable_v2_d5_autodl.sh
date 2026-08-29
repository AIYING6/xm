#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_stable_v2_d5_pilot}"
MAX_PARALLEL="${MAX_PARALLEL:-9}"
PYTHON_BIN="${PYTHON_BIN:-python}"

[[ "$MAX_PARALLEL" == "9" ]] || { echo "D5 freezes the maximum possible nine-way launch" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }
available_kb=$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')
[[ "$available_kb" -ge 15728640 ]] || { echo "need at least 15 GiB free" >&2; exit 2; }

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"
mkdir -p "$OUT/launcher_logs" "$OUT/diagnostics/preflight" "$OUT/diagnostics/technical"

if ! "$PYTHON_BIN" -c 'import pytest' >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pip install --disable-pip-version-check -q 'pytest>=8,<9'
fi
"$PYTHON_BIN" scripts/verify_drtp_stable_v2_d5_preflight.py \
  --output "$OUT/diagnostics/preflight/D5_PREFLIGHT.json"
"$PYTHON_BIN" scripts/run_drtp_stable_v2_d4_technical_audit.py \
  --output "$OUT/diagnostics/technical/D4_TECHNICAL_AUDIT.json" \
  --decision "$OUT/diagnostics/technical/D4_DECISION.json"
"$PYTHON_BIN" -m pytest -q tests/test_drtp_stable_v2_d5_contract.py \
  > "$OUT/diagnostics/technical/D5_CONTRACT_TEST.txt"

export ROOT OUT PYTHON_BIN
printf '%s\n' \
  utr_sg:3201 utr_sg:3202 utr_sg:3203 \
  drtp_sg:3201 drtp_sg:3202 drtp_sg:3203 \
  drtp_klb_sg:3201 drtp_klb_sg:3202 drtp_klb_sg:3203 \
  | xargs -r -n 1 -P "$MAX_PARALLEL" bash -c '
      spec="$1"; arm="${spec%%:*}"; seed="${spec##*:}"
      "$PYTHON_BIN" "$ROOT/scripts/run_drtp_stable_v2_d5_single.py" \
        --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
        >"$OUT/launcher_logs/${arm}_seed${seed}.out" \
        2>"$OUT/launcher_logs/${arm}_seed${seed}.err"
    ' _ || { echo "D5 training failed; evaluation was not started" >&2; exit 3; }

"$PYTHON_BIN" scripts/run_drtp_stable_v2_d5_evaluation.py \
  --output-root "$OUT" --workers 9 --execute
"$PYTHON_BIN" scripts/aggregate_drtp_stable_v2_d5_pilot.py \
  --output-root "$OUT" \
  --technical-audit "$OUT/diagnostics/technical/D4_TECHNICAL_AUDIT.json" \
  --execute

tar -czf "$ROOT/drtp_stable_v2_d5_pilot_05m_results.tar.gz" \
  -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/drtp_stable_v2_d5_pilot_05m_results.tar.gz" \
  > "$ROOT/drtp_stable_v2_d5_pilot_05m_results.tar.gz.sha256"
cp "$ROOT/drtp_stable_v2_d5_pilot_05m_results.tar.gz.sha256" \
  "$OUT/diagnostics/stable_v2_d5_pilot_gate/RESULT_ARCHIVE_SHA256.txt"

echo "D5 pilot complete; no continuation, rerun, threshold change, or mainline-A mutation was started."
