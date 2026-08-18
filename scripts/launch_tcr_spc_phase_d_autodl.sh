#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
MAX_PARALLEL="${MAX_PARALLEL:-4}"
EVAL_WORKERS="${EVAL_WORKERS:-4}"
SOURCE_ROOT="${PHASE_C_SOURCE_ROOT:-results/development/tcr_spc_phase_c_1m}"
OUTPUT_ROOT="${PHASE_D_OUTPUT_ROOT:-results/development/tcr_spc_phase_d_3m}"

if [[ ! -d "$SOURCE_ROOT" ]]; then
  echo "missing Phase-C source root: $SOURCE_ROOT" >&2
  exit 2
fi
if [[ -f "$SOURCE_ROOT/tape_manifest.json" ]]; then
  mkdir -p "$OUTPUT_ROOT"
  cp -n "$SOURCE_ROOT/tape_manifest.json" "$OUTPUT_ROOT/tape_manifest.json"
else
  echo "missing frozen Phase-C development tape manifest" >&2
  exit 2
fi

mkdir -p "$OUTPUT_ROOT/logs"
declare -a pids=()
declare -a labels=()
launch_one() {
  local arm="$1" seed="$2" label="${arm}_seed${seed}"
  "$PYTHON_BIN" scripts/run_tcr_spc_phase_d_continuation.py \
    --source-root "$SOURCE_ROOT" --output-root "$OUTPUT_ROOT" \
    --arm "$arm" --seed "$seed" --execute \
    > "$OUTPUT_ROOT/logs/${label}.out" 2> "$OUTPUT_ROOT/logs/${label}.err" &
  pids+=("$!")
  labels+=("$label")
  echo "launched $label pid=${pids[-1]}"
}
wait_one() {
  local pid="${pids[0]}" label="${labels[0]}"
  if ! wait "$pid"; then
    echo "Phase-D continuation failed: $label" >&2
    exit 1
  fi
  pids=("${pids[@]:1}")
  labels=("${labels[@]:1}")
}

for arm in utr_sg spc_sg tcr_sg; do
  for seed in 2002 2101 2102 2103 2104; do
    while [[ "${#pids[@]}" -ge "$MAX_PARALLEL" ]]; do wait_one; done
    launch_one "$arm" "$seed"
  done
done
while [[ "${#pids[@]}" -gt 0 ]]; do wait_one; done

"$PYTHON_BIN" scripts/run_tcr_spc_phase_c_evaluation.py \
  --output-root "$OUTPUT_ROOT" --workers "$EVAL_WORKERS" --phase-d --execute \
  > "$OUTPUT_ROOT/phase_d_evaluation.out" 2> "$OUTPUT_ROOT/phase_d_evaluation.err"

"$PYTHON_BIN" scripts/aggregate_tcr_spc_phase_d.py \
  --results-root "$OUTPUT_ROOT" \
  --report-path docs/TCR_SPC_PHASE_D_3M_CONTINUATION_REPORT.md \
  > "$OUTPUT_ROOT/phase_d_aggregate.out" 2> "$OUTPUT_ROOT/phase_d_aggregate.err"

echo "Phase D complete at 3,000,064 steps; no 3M-to-5M continuation was started."
