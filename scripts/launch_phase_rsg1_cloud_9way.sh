#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/phase_rsg1_development_smoke}"
AUTO_SHUTDOWN="${AUTO_SHUTDOWN:-1}"

if [ -e "$OUTPUT_ROOT" ]; then
  echo "Refusing to overwrite existing output: $OUTPUT_ROOT" >&2
  exit 2
fi
mkdir -p logs

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"

methods=(mappo matched_single_graph rsg_tc)
seeds=(1501 1502 1503)
pids=()
status=0

for method in "${methods[@]}"; do
  for seed in "${seeds[@]}"; do
    log="logs/rsg1_${method}_seed${seed}"
    nohup "$PYTHON_BIN" scripts/run_phase_rsg1_single_run.py \
      --method "$method" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute \
      > "${log}.out" 2> "${log}.err" &
    pids+=("$!")
    echo "started method=$method seed=$seed pid=${pids[-1]}"
  done
done

for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    status=1
  fi
done

if [ "$status" -eq 0 ]; then
  "$PYTHON_BIN" scripts/aggregate_phase_rsg1_results.py --output-root "$OUTPUT_ROOT" || status=$?
fi

sync
if [ "$AUTO_SHUTDOWN" = "1" ]; then
  shutdown -h now
fi
exit "$status"
