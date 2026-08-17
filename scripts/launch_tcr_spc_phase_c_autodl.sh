#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
MAX_PARALLEL="${MAX_PARALLEL:-4}"
EVAL_WORKERS="${EVAL_WORKERS:-4}"
ROOT="${PHASE_C_OUTPUT_ROOT:-results/development/tcr_spc_phase_c_1m}"

if [[ "$MAX_PARALLEL" -lt 1 || "$EVAL_WORKERS" -lt 1 ]]; then
  echo "MAX_PARALLEL and EVAL_WORKERS must be positive" >&2
  exit 2
fi

mkdir -p "$ROOT/logs"
"$PYTHON_BIN" scripts/verify_tcr_spc_phase_c_preflight.py --output-root "$ROOT" --execute
"$PYTHON_BIN" scripts/create_tcr_spc_phase_c_tape.py --output-root "$ROOT" --execute

declare -a pids=()
declare -a labels=()
launch_one() {
  local arm="$1" seed="$2" label="${arm}_seed${seed}"
  "$PYTHON_BIN" scripts/run_tcr_spc_phase_c_single.py --arm "$arm" --seed "$seed" --output-root "$ROOT" --execute \
    > "$ROOT/${label}.out" 2> "$ROOT/${label}.err" &
  local pid="$!"
  pids+=("$pid")
  labels+=("$label")
  echo "launched $label pid=$pid"
}
wait_one() {
  local pid="${pids[0]}" label="${labels[0]}"
  if ! wait "$pid"; then
    echo "Phase-C trajectory failed: $label" >&2
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

"$PYTHON_BIN" scripts/run_tcr_spc_phase_c_evaluation.py --output-root "$ROOT" --workers "$EVAL_WORKERS" --execute \
  > "$ROOT/phase_c_evaluation.out" 2> "$ROOT/phase_c_evaluation.err"
"$PYTHON_BIN" scripts/aggregate_tcr_spc_phase_c.py --results-root "$ROOT" \
  --report-path docs/TCR_SPC_PHASE_C_1M_STABILITY_SCREEN_REPORT.md \
  > "$ROOT/phase_c_aggregate.out" 2> "$ROOT/phase_c_aggregate.err"

echo "Phase C complete at 1M; no continuation was started."
