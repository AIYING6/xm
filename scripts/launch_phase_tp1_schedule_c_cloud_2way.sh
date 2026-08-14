#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/phase_tp1_schedule_c}"
PYTHON_BIN="${PYTHON_BIN:-python}"
AUTO_SHUTDOWN="${AUTO_SHUTDOWN:-1}"

if [[ -e "$OUTPUT_ROOT" ]]; then
  echo "Refusing to overwrite existing output: $OUTPUT_ROOT" >&2
  exit 1
fi

mkdir -p logs "$OUTPUT_ROOT"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"

pids=()
for seed in 1601 1602; do
  nohup "$PYTHON_BIN" scripts/run_phase_tp1_round_a_single.py \
    --arm ctp_c --seed "$seed" --output-root "$OUTPUT_ROOT" --execute \
    > "logs/tp1_schedule_c_seed${seed}.out" 2> "logs/tp1_schedule_c_seed${seed}.err" &
  pids+=("$!")
done

rc=0
for pid in "${pids[@]}"; do
  wait "$pid" || rc=$?
done
if [[ "$rc" -ne 0 ]]; then
  echo "Schedule C training failed with status $rc" >&2
  exit "$rc"
fi

"$PYTHON_BIN" scripts/aggregate_phase_tp1_schedule_c.py --results-root "$OUTPUT_ROOT"
sync
if [[ "$AUTO_SHUTDOWN" == "1" ]]; then
  shutdown -h now
fi
