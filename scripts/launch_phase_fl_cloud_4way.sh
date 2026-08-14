#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/phase_fl_failure_learnability}"
PYTHON_BIN="${PYTHON_BIN:-python}"
AUTO_SHUTDOWN="${AUTO_SHUTDOWN:-1}"
RESULT_ARCHIVE="${RESULT_ARCHIVE:-/root/autodl-tmp/phase_fl_results.tar.gz}"

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

"$PYTHON_BIN" scripts/create_phase_fl_tape.py --output-root "$OUTPUT_ROOT"

pids=()
for spec in \
  "fl_nominal_expert 1801" \
  "fl_nominal_expert 1802" \
  "fl_f0_expert 1801" \
  "fl_f0_expert 1802"; do
  read -r arm seed <<< "$spec"
  nohup "$PYTHON_BIN" scripts/run_phase_fl_single.py \
    --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute \
    > "logs/phase_fl_${arm}_seed${seed}.out" \
    2> "logs/phase_fl_${arm}_seed${seed}.err" &
  pids+=("$!")
done

rc=0
for pid in "${pids[@]}"; do
  wait "$pid" || rc=$?
done
if [[ "$rc" -ne 0 ]]; then
  echo "Phase FL training failed with status $rc" >&2
  exit "$rc"
fi

"$PYTHON_BIN" scripts/aggregate_phase_fl.py --results-root "$OUTPUT_ROOT"
tar -czf "$RESULT_ARCHIVE" "$OUTPUT_ROOT"
sha256sum "$RESULT_ARCHIVE"
sync
if [[ "$AUTO_SHUTDOWN" == "1" ]]; then
  shutdown -h now
fi
