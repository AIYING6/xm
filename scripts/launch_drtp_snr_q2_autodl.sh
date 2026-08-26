#!/usr/bin/env bash
# Authorized prospective UTR/SNR/DRTP 15-run Q2 mechanism comparator.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-results/formal/drtp_snr_q2_mechanism_comparator}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
EVAL_WORKERS="${EVAL_WORKERS:-8}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-16}"
GPU_IDS="${GPU_IDS:-0}"

if [[ "$MAX_PARALLEL" -lt 1 || "$EVAL_WORKERS" -lt 1 ]]; then echo "MAX_PARALLEL and EVAL_WORKERS must be positive" >&2; exit 2; fi
if [[ -e "$OUTPUT_ROOT" && -n "$(find "$OUTPUT_ROOT" -mindepth 1 -print -quit)" ]]; then echo "Refusing to overwrite non-empty output root: $OUTPUT_ROOT" >&2; exit 2; fi
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(( CPU_THREADS_TOTAL / MAX_PARALLEL ))}"; if [[ "$OMP_NUM_THREADS" -lt 1 ]]; then export OMP_NUM_THREADS=1; fi
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$OMP_NUM_THREADS}"
mkdir -p "$OUTPUT_ROOT"; IFS=',' read -r -a GPU_ARRAY <<< "$GPU_IDS"

"$PYTHON_BIN" scripts/verify_drtp_snr_q2_preflight.py --output "$OUTPUT_ROOT/snr_preflight.json" > "$OUTPUT_ROOT/snr_preflight.out" 2> "$OUTPUT_ROOT/snr_preflight.err"
"$PYTHON_BIN" scripts/create_drtp_snr_q2_tape.py --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/tape_creation.out" 2> "$OUTPUT_ROOT/tape_creation.err"

running=0; launch_index=0
for arm in utr_sg snr_sg drtp_sg; do
  for seed in 2401 2402 2403 2404 2405; do
    gpu="${GPU_ARRAY[$((launch_index % ${#GPU_ARRAY[@]}))]}"
    CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON_BIN" scripts/run_drtp_snr_q2_formal_single.py --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute > "$OUTPUT_ROOT/${arm}_${seed}.out" 2> "$OUTPUT_ROOT/${arm}_${seed}.err" &
    launch_index=$((launch_index + 1)); running=$((running + 1)); if [[ "$running" -ge "$MAX_PARALLEL" ]]; then wait -n; running=$((running - 1)); fi
  done
done
wait
"$PYTHON_BIN" scripts/run_drtp_snr_q2_evaluation.py --output-root "$OUTPUT_ROOT" --workers "$EVAL_WORKERS" --gpu-ids "$GPU_IDS" --execute > "$OUTPUT_ROOT/snr_evaluation.out" 2> "$OUTPUT_ROOT/snr_evaluation.err"
"$PYTHON_BIN" scripts/aggregate_drtp_snr_q2.py --results-root "$OUTPUT_ROOT" --report-path "$OUTPUT_ROOT/DRTP_SNR_Q2_MECHANISM_COMPARATOR_REPORT.md" > "$OUTPUT_ROOT/snr_aggregate.out" 2> "$OUTPUT_ROOT/snr_aggregate.err"
tar -czf "${OUTPUT_ROOT}.tar.gz" "$OUTPUT_ROOT"; sha256sum "${OUTPUT_ROOT}.tar.gz" > "${OUTPUT_ROOT}.tar.gz.sha256"
echo "SNR mechanism comparator completed, packaged, and stopped. No follow-on stage was started."
