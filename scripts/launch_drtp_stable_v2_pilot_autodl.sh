#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-$ROOT/results/development/drtp_stable_v2_pilot}"
MAX_PARALLEL="${MAX_PARALLEL:-9}"
PYTHON_BIN="${PYTHON_BIN:-python}"

[[ "$MAX_PARALLEL" == "9" ]] || { echo "Stable-v2 pilot freezes all-nine parallel launch" >&2; exit 2; }
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }
available_kb=$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')
[[ "$available_kb" -ge 15728640 ]] || { echo "need at least 15 GiB free" >&2; exit 2; }

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"
mkdir -p "$OUT/launcher_logs" "$OUT/diagnostics/preflight" "$OUT/diagnostics/technical"

"$PYTHON_BIN" scripts/verify_drtp_stable_v2_pilot_preflight.py \
  --output "$OUT/diagnostics/preflight/D2_PREFLIGHT.json"
"$PYTHON_BIN" scripts/run_drtp_stable_v2_technical_audit.py \
  --output "$OUT/diagnostics/technical/D1_TECHNICAL_AUDIT.json"

export ROOT OUT PYTHON_BIN
printf '%s\n' \
  utr_sg:3101 utr_sg:3102 utr_sg:3103 \
  drtp_sg:3101 drtp_sg:3102 drtp_sg:3103 \
  drtp_klr_sg:3101 drtp_klr_sg:3102 drtp_klr_sg:3103 \
  | xargs -r -n 1 -P "$MAX_PARALLEL" bash -c '
      spec="$1"; arm="${spec%%:*}"; seed="${spec##*:}"
      "$PYTHON_BIN" "$ROOT/scripts/run_drtp_stable_v2_pilot_single.py" \
        --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
        >"$OUT/launcher_logs/${arm}_seed${seed}.out" \
        2>"$OUT/launcher_logs/${arm}_seed${seed}.err"
    ' _ || { echo "Stable-v2 pilot training failed; evaluation was not started" >&2; exit 3; }

"$PYTHON_BIN" scripts/run_drtp_stable_v2_pilot_evaluation.py \
  --output-root "$OUT" --workers 9 --execute
"$PYTHON_BIN" scripts/aggregate_drtp_stable_v2_pilot.py \
  --output-root "$OUT" \
  --technical-audit "$OUT/diagnostics/technical/D1_TECHNICAL_AUDIT.json" \
  --execute

tar -czf "$ROOT/drtp_stable_v2_pilot_05m_results.tar.gz" \
  -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "$ROOT/drtp_stable_v2_pilot_05m_results.tar.gz" \
  > "$ROOT/drtp_stable_v2_pilot_05m_results.tar.gz.sha256"
cp "$ROOT/drtp_stable_v2_pilot_05m_results.tar.gz.sha256" \
  "$OUT/diagnostics/stable_v2_pilot_gate/RESULT_ARCHIVE_SHA256.txt"

echo "Stable-v2 pilot complete; no 1M/3M continuation or threshold change was started."
