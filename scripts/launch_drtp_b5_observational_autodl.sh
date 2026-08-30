#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUTPUT_ROOT:-${ROOT}/results/development/drtp_b5_observational}"
MAX_PARALLEL="${MAX_PARALLEL:-10}"
WORKERS="${WORKERS:-20}"
PYTHON_BIN="${PYTHON_BIN:-python}"

[[ "${B5_EXECUTION_AUTHORIZED:-NO}" == "YES" ]] || {
  echo "B5 cloud execution requires explicit B5_EXECUTION_AUTHORIZED=YES" >&2
  exit 2
}
[[ "$MAX_PARALLEL" =~ ^[0-9]+$ && "$MAX_PARALLEL" -ge 10 ]] || {
  echo "maximum concurrency requires all 10 frozen trajectories (MAX_PARALLEL>=10)" >&2
  exit 2
}
[[ "$WORKERS" =~ ^[0-9]+$ && "$WORKERS" -gt 0 ]] || {
  echo "WORKERS must be positive" >&2
  exit 2
}
[[ ! -e "$OUT" ]] || { echo "refusing existing output root: $OUT" >&2; exit 2; }

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"

"$PYTHON_BIN" scripts/verify_drtp_b5_observational_preflight.py
mkdir -p "$OUT/launcher_logs"

pids=()
for arm in utr_sg drtp_sg; do
  for seed in 3601 3602 3603 3604 3605; do
    "$PYTHON_BIN" scripts/run_drtp_b5_observational_single.py \
      --arm "$arm" --seed "$seed" --output-root "$OUT" --execute \
      >"$OUT/launcher_logs/${arm}_seed${seed}.out" \
      2>"$OUT/launcher_logs/${arm}_seed${seed}.err" &
    pids+=("$!")
  done
done

failed=0
for pid in "${pids[@]}"; do
  wait "$pid" || failed=1
done
[[ "$failed" == 0 ]] || {
  echo "B5 training failed; evaluation and aggregation were not started" >&2
  exit 3
}

"$PYTHON_BIN" scripts/run_drtp_b5_observational_evaluation.py \
  --output-root "$OUT" --workers "$WORKERS" --execute
"$PYTHON_BIN" scripts/aggregate_drtp_b5_observational.py \
  --output-root "$OUT" --execute

tar -czf "${OUT}.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "${OUT}.tar.gz" > "${OUT}.tar.gz.sha256"
echo "B5 observational cohort complete; no algorithm modification or continuation was started."
