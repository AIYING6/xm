#!/usr/bin/env bash
set -euo pipefail

# Cloud launcher for one RTX 4090. Hardware parallelism is isolated from the
# frozen scientific protocol: num_envs/rollout_steps/updates/seeds are fixed.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
GPU_ID="${GPU_ID:-0}"
RUN_CONCURRENCY="${RUN_CONCURRENCY:-2}"
OUT_ROOT="${OUT_ROOT:-${ROOT}/results/canonical_v2/formal/wave1}"

export CUDA_VISIBLE_DEVICES="${GPU_ID}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export PYTHONUNBUFFERED=1

mkdir -p "${ROOT}/results/canonical_v2/manifests/wave1/cloud_4090"

run_one() {
  local method="$1" seed="$2" encoder="$3"
  local out="${OUT_ROOT}/${method}/seed${seed}"
  mkdir -p "${out}"
  echo "[$(date --iso-8601=seconds)] start method=${method} seed=${seed} encoder=${encoder}" \
    | tee "${out}/cloud_launch.log"
  "${PYTHON_BIN}" -B "${ROOT}/scripts/train_ri_gmappo.py" \
    --seed "${seed}" --env-name 3d_intercept --target-policy straight \
    --strict-target-sensing --agent-target-info-bottleneck \
    --communication-dropout-prob 0.30 --message-delay-steps 2 \
    --failed-blue-agent 1 --node-failure-start-step 40 \
    --node-failure-duration-steps 80 --graph-encoder "${encoder}" \
    --multi-relation-global-residual-weight 1.0 \
    --num-envs 4 --rollout-steps 64 --updates 3907 \
    --eval-interval 10 --eval-episodes 20 --save-interval 10 \
    --save-snapshots --hidden-dim 64 --device cuda \
    --out-dir "${out}" \
    >"${out}/process.stdout.log" 2>"${out}/process.stderr.log"
}

jobs=()
for method in full mappo; do
  encoder=multi_relation
  [[ "${method}" == "mappo" ]] && encoder=no_graph
  for seed in 0 1 2 3 4; do
    run_one "${method}" "${seed}" "${encoder}" &
    jobs+=("$!")
    while (( $(jobs -rp | wc -l) >= RUN_CONCURRENCY )); do
      wait -n
    done
  done
done
for job in "${jobs[@]}"; do wait "${job}"; done
echo "[$(date --iso-8601=seconds)] Wave 1 complete"
