#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; OUT="${OUTPUT_ROOT:-$ROOT/results/development/cv_drtp_pilot}"; MAX_PARALLEL="${MAX_PARALLEL:-9}"; PYTHON_BIN="${PYTHON_BIN:-python}"
[[ "$MAX_PARALLEL" == "9" ]] || { echo "Frozen CV pilot requires MAX_PARALLEL=9" >&2; exit 2; }; [[ ! -e "$OUT" ]] || { echo "refusing existing output root" >&2; exit 2; }; [[ $(df -Pk "$ROOT"|awk 'NR==2{print $4}') -ge 15728640 ]] || { echo "need 15GiB free" >&2; exit 2; }
export PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1; mkdir -p "$OUT/launcher_logs"; cd "$ROOT"; export ROOT OUT PYTHON_BIN
"$PYTHON_BIN" -m pytest -q tests/test_cv_drtp_d1.py
printf '%s\n' $(for arm in utr_sg drtp_sg cv_drtp_sg; do for seed in {4301..4310}; do echo "$arm:$seed"; done; done) | xargs -n1 -P "$MAX_PARALLEL" bash -c 'z="$1"; arm="${z%%:*}"; seed="${z##*:}"; "$PYTHON_BIN" "$ROOT/scripts/run_cv_drtp_pilot.py" train --arm "$arm" --seed "$seed" --output-root "$OUT" --execute >"$OUT/launcher_logs/${arm}_seed${seed}.out" 2>"$OUT/launcher_logs/${arm}_seed${seed}.err"' _
"$PYTHON_BIN" scripts/run_cv_drtp_pilot.py evaluate --output-root "$OUT" --workers 9 --execute
"$PYTHON_BIN" scripts/run_cv_drtp_pilot.py aggregate --output-root "$OUT" --execute
tar -czf "$ROOT/cv_drtp_pilot_05m_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"; sha256sum "$ROOT/cv_drtp_pilot_05m_results.tar.gz" > "$ROOT/cv_drtp_pilot_05m_results.tar.gz.sha256"
echo "CV-DRTP pilot complete; no continuation started."
