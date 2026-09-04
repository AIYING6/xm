#!/usr/bin/env bash
# Frozen TATG pilot training launcher.  It contains no evaluation phase.
set -euo pipefail

: "${OUTPUT_ROOT:=results/development/tatg_mappo_pilot}"
: "${MAX_PARALLEL:=4}"
: "${PYTHON_BIN:=python}"
: "${OMP_NUM_THREADS:=1}"
: "${MKL_NUM_THREADS:=1}"
: "${OPENBLAS_NUM_THREADS:=1}"
: "${NUMEXPR_NUM_THREADS:=1}"
export OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS NUMEXPR_NUM_THREADS

case "$MAX_PARALLEL" in
  ''|*[!0-9]*) echo "MAX_PARALLEL must be a positive integer" >&2; exit 2 ;;
esac
if [ "$MAX_PARALLEL" -lt 1 ]; then
  echo "MAX_PARALLEL must be a positive integer" >&2
  exit 2
fi

mkdir -p "$OUTPUT_ROOT"
"$PYTHON_BIN" scripts/run_tatg_mappo_pilot_single.py preflight --output-root "$OUTPUT_ROOT" \
  > "$OUTPUT_ROOT/TATG_PILOT_P2_RUNNER_PREFLIGHT.json"

run_one() {
  local arm="$1"
  local seed="$2"
  local run_dir="$OUTPUT_ROOT/runs/$arm/seed$seed"
  if [ -e "$run_dir" ]; then
    echo "refusing to overwrite frozen pilot trajectory: $run_dir" >&2
    return 1
  fi
  "$PYTHON_BIN" scripts/run_tatg_mappo_pilot_single.py train \
    --arm "$arm" --seed "$seed" --output-root "$OUTPUT_ROOT" --execute \
    > "$OUTPUT_ROOT/${arm}_seed${seed}.out" \
    2> "$OUTPUT_ROOT/${arm}_seed${seed}.err"
}

arms=(utr_snapshot_sg tatg_cetm_utr tatg_snapshot_gru_utr tatg_zero_residual_utr)
seeds=(75011 75012 75013)
for arm in "${arms[@]}"; do
  for seed in "${seeds[@]}"; do
    while [ "$(jobs -rp | wc -l)" -ge "$MAX_PARALLEL" ]; do
      wait -n
    done
    run_one "$arm" "$seed" &
  done
done
wait

completed="$(find "$OUTPUT_ROOT/runs" -name run_manifest.json -type f -print0 | xargs -0 grep -l '"status": "completed"' | wc -l)"
if [ "$completed" -ne 12 ]; then
  echo "expected 12 completed pilot trajectories, found $completed" >&2
  exit 1
fi
if [ -e "$OUTPUT_ROOT/evaluations" ]; then
  echo "training launcher must not create an evaluation directory" >&2
  exit 1
fi
printf '{"status":"TATG_PILOT_TRAINING_COMPLETE","trajectories":12,"evaluation_started":false,"automatic_continuation":false}\n' \
  > "$OUTPUT_ROOT/TATG_PILOT_TRAINING_COMPLETE.json"
