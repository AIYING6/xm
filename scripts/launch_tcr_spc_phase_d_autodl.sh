#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
MAX_PARALLEL="${MAX_PARALLEL:-4}"
EVAL_WORKERS="${EVAL_WORKERS:-4}"
SOURCE_ROOT="${PHASE_C_SOURCE_ROOT:-results/development/tcr_spc_phase_c_1m}"
ROOT_OUTPUT="${PHASE_D_ROOT_OUTPUT:-results/development/phase_d}"
TWO_M_ROOT="${PHASE_D_2M_OUTPUT_ROOT:-${ROOT_OUTPUT}/phase_d_2m}"
THREE_M_ROOT="${PHASE_D_3M_OUTPUT_ROOT:-${ROOT_OUTPUT}/phase_d_3m}"

if [[ ! -d "$SOURCE_ROOT" ]]; then
  echo "missing Phase-C source root: $SOURCE_ROOT" >&2
  exit 2
fi
if [[ ! -f "$SOURCE_ROOT/tape_manifest.json" ]]; then
  echo "missing frozen Phase-C development tape manifest" >&2
  exit 2
fi

run_stage() {
  local stage="$1" source_root="$2" output_root="$3"
  if [[ ! -f "$source_root/tape_manifest.json" ]]; then
    echo "missing frozen tape manifest in $source_root" >&2
    exit 2
  fi
  mkdir -p "$output_root/logs"
  cp -n "$source_root/tape_manifest.json" "$output_root/tape_manifest.json"
  declare -a pids=()
  declare -a labels=()
  launch_one() {
    local arm="$1" seed="$2" label="${arm}_seed${seed}"
    "$PYTHON_BIN" scripts/run_tcr_spc_phase_d_continuation.py \
      --source-root "$source_root" --output-root "$output_root" \
      --arm "$arm" --seed "$seed" --stage "$stage" --execute \
      > "$output_root/logs/${label}.out" 2> "$output_root/logs/${label}.err" &
    pids+=("$!")
    labels+=("$label")
    echo "launched $stage $label pid=${pids[-1]}"
  }
  wait_one() {
    local pid="${pids[0]}" label="${labels[0]}"
    if ! wait "$pid"; then
      echo "Phase-D $stage continuation failed: $label" >&2
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
}

run_stage 2m "$SOURCE_ROOT" "$TWO_M_ROOT"
"$PYTHON_BIN" scripts/run_tcr_spc_phase_c_evaluation.py \
  --output-root "$TWO_M_ROOT" --workers "$EVAL_WORKERS" \
  --phase-d --phase-d-budget 2m --execute \
  > "$TWO_M_ROOT/phase_d_evaluation.out" 2> "$TWO_M_ROOT/phase_d_evaluation.err"
"$PYTHON_BIN" scripts/aggregate_tcr_spc_phase_d_2m.py \
  --results-root "$TWO_M_ROOT" \
  --report-path docs/TCR_SPC_PHASE_D_2M_INTERIM_STOP_LOSS_REPORT.md \
  > "$TWO_M_ROOT/phase_d_aggregate.out" 2> "$TWO_M_ROOT/phase_d_aggregate.err"
decision="$($PYTHON_BIN -c 'import json,sys; print(json.load(open(sys.argv[1]))["decision"])' \
  "$TWO_M_ROOT/evaluations/final_2m/PHASE_D_2M_INTERIM_DECISION.json")"
echo "Phase-D 2M interim decision: $decision"
if [[ "$decision" == "STOP_AT_2M" ]]; then
  echo "Phase-D stopped at 2M by the pre-registered futility/stop-loss gate."
  exit 0
fi

run_stage 3m "$TWO_M_ROOT" "$THREE_M_ROOT"
"$PYTHON_BIN" scripts/run_tcr_spc_phase_c_evaluation.py \
  --output-root "$THREE_M_ROOT" --workers "$EVAL_WORKERS" \
  --phase-d --phase-d-budget 3m --execute \
  > "$THREE_M_ROOT/phase_d_evaluation.out" 2> "$THREE_M_ROOT/phase_d_evaluation.err"
"$PYTHON_BIN" scripts/aggregate_tcr_spc_phase_d.py \
  --results-root "$THREE_M_ROOT" \
  --report-path docs/TCR_SPC_PHASE_D_3M_CONTINUATION_REPORT.md \
  > "$THREE_M_ROOT/phase_d_aggregate.out" 2> "$THREE_M_ROOT/phase_d_aggregate.err"
echo "Phase-D complete at 3,000,064 steps; no 3M-to-5M continuation was started."
