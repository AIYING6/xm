#!/usr/bin/env bash
# Frozen MAPPO-NoGraph external-reference controller. Stops after packaging.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/formal/drtp_mappo_nograph_external_5seed}"
MAX_PARALLEL="${MAX_PARALLEL:-5}"
EVAL_WORKERS="${EVAL_WORKERS:-5}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-16}"
GPU_IDS="${GPU_IDS:-0}"

if [[ "$MAX_PARALLEL" -lt 1 || "$EVAL_WORKERS" -lt 1 ]]; then echo "parallel settings must be positive" >&2; exit 2; fi
if [[ -e "$OUTPUT_ROOT" && -n "$(find "$OUTPUT_ROOT" -mindepth 1 -print -quit)" ]]; then echo "Refusing to overwrite: $OUTPUT_ROOT" >&2; exit 2; fi
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(( CPU_THREADS_TOTAL / MAX_PARALLEL ))}"
if [[ "$OMP_NUM_THREADS" -lt 1 ]]; then export OMP_NUM_THREADS=1; fi
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"
mkdir -p "$OUTPUT_ROOT"
IFS=',' read -r -a GPU_ARRAY <<< "$GPU_IDS"
if [[ "${#GPU_ARRAY[@]}" -lt 1 ]]; then echo "GPU_IDS must be non-empty" >&2; exit 2; fi

"$PYTHON_BIN" scripts/verify_drtp_mappo_external_contract.py --output "$OUTPUT_ROOT/external_preflight.json" > "$OUTPUT_ROOT/external_preflight.out" 2> "$OUTPUT_ROOT/external_preflight.err"
"$PYTHON_BIN" scripts/create_drtp_utr_q2_formal_tape.py --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/tape_verification.out" 2> "$OUTPUT_ROOT/tape_verification.err"

running=0; index=0
for seed in 2301 2302 2303 2304 2305; do
  gpu="${GPU_ARRAY[$((index % ${#GPU_ARRAY[@]}))]}"
  CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON_BIN" scripts/run_drtp_mappo_external_single.py --seed "$seed" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/mappo_ng_${seed}.out" 2> "$OUTPUT_ROOT/mappo_ng_${seed}.err" &
  index=$((index + 1)); running=$((running + 1))
  if [[ "$running" -ge "$MAX_PARALLEL" ]]; then wait -n; running=$((running - 1)); fi
done
wait
"$PYTHON_BIN" scripts/run_drtp_mappo_external_evaluation.py --output-root "$OUTPUT_ROOT" --workers "$EVAL_WORKERS" --gpu-ids "$GPU_IDS" --execute > "$OUTPUT_ROOT/mappo_evaluation.out" 2> "$OUTPUT_ROOT/mappo_evaluation.err"
"$PYTHON_BIN" scripts/aggregate_drtp_mappo_external.py --results-root "$OUTPUT_ROOT" --report-path "$OUTPUT_ROOT/DRTP_MAPPO_EXTERNAL_REFERENCE_REPORT.md" > "$OUTPUT_ROOT/mappo_aggregate.out" 2> "$OUTPUT_ROOT/mappo_aggregate.err"
tar -czf "${OUTPUT_ROOT}.tar.gz" "$OUTPUT_ROOT"
sha256sum "${OUTPUT_ROOT}.tar.gz" > "${OUTPUT_ROOT}.tar.gz.sha256"
echo "MAPPO-NoGraph external reference completed, packaged, and stopped."
