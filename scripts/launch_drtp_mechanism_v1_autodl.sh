#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_ROOT="${OUTPUT_ROOT:-${PROJECT_ROOT}/results/development/drtp_mechanism_v1}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
PYTHON_BIN="${PYTHON_BIN:-python}"
THREADS="${CPU_THREADS_TOTAL:-10}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

cd "${PROJECT_ROOT}" || exit 1
test -f diagnostics/drtp_mechanism_v1/03_tape/tape_manifest.json || { echo "missing frozen tape" >&2; exit 2; }
test -f diagnostics/drtp_mechanism_v1/04_technical_audit/technical_audit.json || { echo "missing P3 audit" >&2; exit 2; }
grep -q 'P3_TECHNICAL_PASS' diagnostics/drtp_mechanism_v1/04_technical_audit/technical_audit.json || { echo "P3 audit is not PASS" >&2; exit 2; }

echo "DRTP Mechanism V1: max_parallel=${MAX_PARALLEL}, cpu_threads_total=${THREADS}, output=${OUTPUT_ROOT}"
mkdir -p "${OUTPUT_ROOT}/launcher_logs"
running=0
pids=()
names=()
failed=0

for arm in utr_sg drtp_sg; do
  for seed in 2601 2602 2603; do
    while [ "${running}" -ge "${MAX_PARALLEL}" ]; do
      wait "${pids[0]}" || failed=1
      pids=("${pids[@]:1}")
      names=("${names[@]:1}")
      running=$((running - 1))
    done
    name="${arm}_seed${seed}"
    echo "launch ${name}"
    "${PYTHON_BIN}" scripts/run_drtp_mechanism_v1_single.py \
      --arm "${arm}" --seed "${seed}" --output-root "${OUTPUT_ROOT}" --execute \
      > "${OUTPUT_ROOT}/launcher_logs/${name}.out" \
      2> "${OUTPUT_ROOT}/launcher_logs/${name}.err" &
    pids+=("$!")
    names+=("${name}")
    running=$((running + 1))
  done
done

for index in "${!pids[@]}"; do
  wait "${pids[$index]}" || failed=1
done

if [ "${failed}" -ne 0 ]; then
  echo "DRTP Mechanism V1 training failed; no evaluation was started" >&2
  exit 3
fi
echo "DRTP Mechanism V1 training complete; evaluation/aggregation is not started by this launcher."
exit 0
