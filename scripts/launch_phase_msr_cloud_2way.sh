#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/development/phase_msr_mature_shared_policy}"
SPECIALIST_ROOT="${SPECIALIST_ROOT:-$ROOT_DIR/inputs/mature_specialists}"
PYTHON_BIN="${PYTHON_BIN:-python}"
AUTO_SHUTDOWN="${AUTO_SHUTDOWN:-1}"
RESULT_ARCHIVE="${RESULT_ARCHIVE:-/root/autodl-tmp/phase_msr_results.tar.gz}"

if [[ -e "$OUTPUT_ROOT" ]]; then
  echo "Refusing to overwrite existing output: $OUTPUT_ROOT" >&2
  exit 1
fi
for arm in fl_nominal_expert fl_f0_expert; do
  for seed in 1801 1802; do
    test -f "$SPECIALIST_ROOT/$arm/seed$seed/actor_critic_latest.pt"
    test -f "$SPECIALIST_ROOT/$arm/seed$seed/run_manifest.json"
  done
done

mkdir -p logs "$OUTPUT_ROOT"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"

"$PYTHON_BIN" scripts/create_phase_msr_tape.py --output-root "$OUTPUT_ROOT"

pids=()
for seed in 1801 1802; do
  nohup "$PYTHON_BIN" scripts/run_phase_msr_mixed50_single.py \
    --seed "$seed" --output-root "$OUTPUT_ROOT" --execute \
    > "logs/phase_msr_mixed50_seed${seed}.out" \
    2> "logs/phase_msr_mixed50_seed${seed}.err" &
  pids+=("$!")
done

rc=0
for pid in "${pids[@]}"; do
  wait "$pid" || rc=$?
done
if [[ "$rc" -ne 0 ]]; then
  echo "Stage MSR mixed50 training failed with status $rc" >&2
  exit "$rc"
fi

"$PYTHON_BIN" scripts/run_phase_msr_unified_evaluation.py \
  --output-root "$OUTPUT_ROOT" --specialist-root "$SPECIALIST_ROOT"
"$PYTHON_BIN" scripts/aggregate_phase_msr.py --results-root "$OUTPUT_ROOT"
"$PYTHON_BIN" scripts/write_phase_msr_report.py \
  --results-root "$OUTPUT_ROOT" \
  --output docs/PHASE_MSR_MATURE_SHARED_POLICY_REFERENCE_REPORT.md \
  --provenance MSR_CLOUD_PROVENANCE.json
tar -czf "$RESULT_ARCHIVE" "$OUTPUT_ROOT" docs/PHASE_MSR_MATURE_SHARED_POLICY_REFERENCE_REPORT.md
sha256sum "$RESULT_ARCHIVE"
sync
if [[ "$AUTO_SHUTDOWN" == "1" ]]; then
  shutdown -h now
fi
