#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; R1_ROOT="${R1_ROOT:?R1_ROOT required}"; OUT="${OUTPUT_ROOT:-$ROOT/results/forensic/drtp_stable_r1_stage2}"; WORKERS="${WORKERS:-15}"; PYTHON_BIN="${PYTHON_BIN:-python}"
[[ -d "$R1_ROOT/runs" ]] || { echo "missing frozen R1 run root" >&2; exit 2; }; [[ ! -e "$OUT" ]] || { echo "refusing existing forensic output" >&2; exit 2; }
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"; "$PYTHON_BIN" scripts/run_drtp_stable_r1_forensic_evaluation.py --r1-root "$R1_ROOT" --output-root "$OUT" --workers "$WORKERS" --execute
"$PYTHON_BIN" scripts/aggregate_drtp_stable_r1_forensic_stage2.py --r1-root "$R1_ROOT" --output-root "$OUT" --execute
tar -czf "$ROOT/drtp_stable_r1_forensic_stage2_results.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"; sha256sum "$ROOT/drtp_stable_r1_forensic_stage2_results.tar.gz" > "$ROOT/drtp_stable_r1_forensic_stage2_results.tar.gz.sha256"
echo 'Stage-2 forensic complete; no training or continuation started.'
