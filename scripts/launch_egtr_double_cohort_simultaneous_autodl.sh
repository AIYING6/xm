#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/egtr_double_cohort_simultaneous}"
MAX_PARALLEL="${MAX_PARALLEL:-20}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-20}"
[[ "$MAX_PARALLEL" -ge 1 && "$MAX_PARALLEL" -le 30 ]] || { echo "MAX_PARALLEL must be 1..30" >&2; exit 2; }
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$((CPU_THREADS_TOTAL/MAX_PARALLEL))}"
[[ "$OMP_NUM_THREADS" -ge 1 ]] || export OMP_NUM_THREADS=1
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-$OMP_NUM_THREADS}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-$OMP_NUM_THREADS}"
[[ ! -e "$OUTPUT_ROOT/runs" ]] || { echo "runs already exist" >&2; exit 2; }
mkdir -p "$OUTPUT_ROOT"
"$PYTHON_BIN" scripts/run_egtr_double_cohort_preregistration_audit.py --output-root results/development/egtr_double_cohort_preregistration --execute > "$OUTPUT_ROOT/p0.out"
"$PYTHON_BIN" scripts/run_egtr_double_cohort_simultaneous_amendment_audit.py --output-root results/development/egtr_double_cohort_preregistration --execute > "$OUTPUT_ROOT/amendment.out"
"$PYTHON_BIN" scripts/create_egtr_double_cohort_simultaneous_tape.py --output-root "$OUTPUT_ROOT/tape" > "$OUTPUT_ROOT/tape.out"
running=0
for arm in utr_sg drtp_sg egtr_sg; do
  for seed in 71011 71012 71013 71014 71015 71021 71022 71023 71024 71025; do
    "$PYTHON_BIN" scripts/run_egtr_double_cohort_simultaneous_single.py --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/${arm}_${seed}.out" 2> "$OUTPUT_ROOT/${arm}_${seed}.err" &
    running=$((running+1))
    if [[ "$running" -ge "$MAX_PARALLEL" ]]; then
      wait -n
      running=$((running-1))
    fi
  done
done
wait
echo "Both cohorts trained; running fixed final evaluation only."
"$PYTHON_BIN" scripts/run_egtr_double_cohort_simultaneous_evaluation.py --trained-root "$OUTPUT_ROOT" --output-root "$OUTPUT_ROOT/evaluations/final_10m" --workers "$MAX_PARALLEL" --execute > "$OUTPUT_ROOT/evaluation.out" 2> "$OUTPUT_ROOT/evaluation.err"
"$PYTHON_BIN" scripts/aggregate_egtr_double_cohort_simultaneous.py --evaluation-root "$OUTPUT_ROOT/evaluations/final_10m" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/aggregate.out" 2> "$OUTPUT_ROOT/aggregate.err"
