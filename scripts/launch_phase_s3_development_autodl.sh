#!/usr/bin/env bash
# Frozen S3 development-only cloud launcher.  Six concurrent processes are
# the maximum approved concurrency for one 16-vCPU / single-4090 instance.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-16}"
CPU_THREADS_PER_RUN="${CPU_THREADS_PER_RUN:-2}"
AUTO_SHUTDOWN="${AUTO_SHUTDOWN:-1}"
RESULT_ROOT="$ROOT/results/development/phase_s3_three_method_smoke"

[[ "$MAX_PARALLEL" == "6" ]] || { echo "S3 contract freezes MAX_PARALLEL=6" >&2; exit 2; }
[[ "$CPU_THREADS_PER_RUN" == "2" ]] || { echo "S3 contract freezes CPU_THREADS_PER_RUN=2" >&2; exit 2; }
[[ ! -e "$RESULT_ROOT/runs" ]] || { echo "Refusing to overwrite S3 runs: $RESULT_ROOT/runs" >&2; exit 3; }

mkdir -p "$RESULT_ROOT/logs"
GIT_SHA="$(git -C "$ROOT" rev-parse HEAD)"
TAG_SHA="$(git -C "$ROOT" rev-parse S3_DEVELOPMENT_LAUNCH_READY^{} 2>/dev/null || true)"
[[ -n "$TAG_SHA" && "$GIT_SHA" == "$TAG_SHA" ]] || {
  echo "HEAD must equal S3_DEVELOPMENT_LAUNCH_READY tag; got $GIT_SHA" >&2; exit 4;
}

ARMS=(
  "mappo:1501" "mappo:1502" "mappo:1503"
  "matched_single_graph:1501" "matched_single_graph:1502" "matched_single_graph:1503"
  "full:1501" "full:1502" "full:1503"
)

run_one() {
  local method="$1" seed="$2"
  local log="$RESULT_ROOT/logs/${method}_seed${seed}.log"
  (
    export OMP_NUM_THREADS="$CPU_THREADS_PER_RUN"
    export MKL_NUM_THREADS="$CPU_THREADS_PER_RUN"
    export OPENBLAS_NUM_THREADS="$CPU_THREADS_PER_RUN"
    export CUDA_DEVICE_MAX_CONNECTIONS=32
    "$PYTHON_BIN" "$ROOT/scripts/run_phase_s3_development_smoke.py" \
      --execute --method "$method" --seed "$seed"
  ) >"$log" 2>&1
}

for ((batch=0; batch<${#ARMS[@]}; batch+=MAX_PARALLEL)); do
  pids=()
  for ((slot=0; slot<MAX_PARALLEL && batch+slot<${#ARMS[@]}; slot++)); do
    IFS=: read -r method seed <<<"${ARMS[batch+slot]}"
    run_one "$method" "$seed" &
    pids+=("$!")
  done
  failed=0
  for pid in "${pids[@]}"; do
    wait "$pid" || failed=1
  done
  [[ "$failed" == "0" ]] || {
    echo "S3 run failed; logs and partial artifacts preserved. No shutdown." >&2
    exit 10
  }
done

for arm in "${ARMS[@]}"; do
  IFS=: read -r method seed <<<"$arm"
  manifest="$RESULT_ROOT/runs/$method/seed$seed/run_manifest.json"
  [[ -f "$manifest" ]] || { echo "Missing manifest: $manifest" >&2; exit 11; }
  "$PYTHON_BIN" -c 'import json,sys; assert json.load(open(sys.argv[1]))["status"] == "completed"' "$manifest"
done

if [[ "$AUTO_SHUTDOWN" == "1" ]]; then
  sync
  shutdown -h now
fi
