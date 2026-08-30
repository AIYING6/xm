#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS_ROOT="${ASSETS_ROOT:?ASSETS_ROOT is required}"
OUT="${OUTPUT_ROOT:-${ROOT}/results/development/drtp_b1_update_sensitivity}"
MAX_PARALLEL="${MAX_PARALLEL:-20}"
WORKERS="${WORKERS:-20}"
PYTHON_BIN="${PYTHON_BIN:-python}"

[[ "${B1_EXECUTION_AUTHORIZED:-NO}" == "YES" ]] || {
  echo "B1 requires explicit B1_EXECUTION_AUTHORIZED=YES" >&2
  exit 2
}
[[ "$MAX_PARALLEL" =~ ^[0-9]+$ && "$MAX_PARALLEL" -gt 0 ]] || {
  echo "MAX_PARALLEL must be positive" >&2
  exit 2
}
[[ "$WORKERS" =~ ^[0-9]+$ && "$WORKERS" -gt 0 ]] || {
  echo "WORKERS must be positive" >&2
  exit 2
}
[[ ! -e "$OUT" ]] || { echo "refusing existing B1 output: $OUT" >&2; exit 2; }

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd "$ROOT"

"$PYTHON_BIN" scripts/verify_drtp_b1_update_sensitivity_preflight.py --assets-root "$ASSETS_ROOT" \
  > b1_preflight.json
mkdir -p "$OUT/launcher_logs"

active=0
failed=0
launch_one() {
  local cohort="$1" arm="$2" seed="$3" family="$4" branch="$5"
  local name="${cohort}_${arm}_seed${seed}_${family}_branch${branch}"
  "$PYTHON_BIN" scripts/run_drtp_b1_update_sensitivity_branch.py \
    --cohort "$cohort" --arm "$arm" --seed "$seed" --family "$family" --branch "$branch" \
    --assets-root "$ASSETS_ROOT" --output-root "$OUT" --execute \
    >"$OUT/launcher_logs/${name}.out" 2>"$OUT/launcher_logs/${name}.err" &
  active=$((active + 1))
}
wait_slot() {
  if ! wait -n; then failed=1; fi
  active=$((active - 1))
}

for binding in \
  "formal_positive_2300:2301 2302 2303 2304 2305" \
  "independent_reversal_2400:2401 2402 2403 2404 2405" \
  "r1_mixed_3000:3001 3002 3003 3004 3005" \
  "b5_mixed_3600:3601 3602 3603 3604 3605"; do
  cohort="${binding%%:*}"
  seeds="${binding#*:}"
  for arm in utr_sg drtp_sg; do
    for seed in $seeds; do
      for family in rollout minibatch; do
        for branch in 0 1 2 3; do
          while (( active >= MAX_PARALLEL )); do wait_slot; done
          launch_one "$cohort" "$arm" "$seed" "$family" "$branch"
        done
      done
    done
  done
done
while (( active > 0 )); do wait_slot; done
[[ "$failed" == 0 ]] || {
  echo "B1 branch execution failed; evaluation was not started" >&2
  exit 3
}

"$PYTHON_BIN" scripts/run_drtp_b1_update_sensitivity_evaluation.py \
  --output-root "$OUT" --workers "$WORKERS" --execute
"$PYTHON_BIN" scripts/aggregate_drtp_b1_update_sensitivity.py \
  --output-root "$OUT" --assets-root "$ASSETS_ROOT" --execute

tar -czf "${OUT}.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")"
sha256sum "${OUT}.tar.gz" > "${OUT}.tar.gz.sha256"
echo "B1 complete and ready for human mechanism review; no algorithm was created."
