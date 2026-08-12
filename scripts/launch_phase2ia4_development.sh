#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
DEVICE="${DEVICE:-cuda}"
MAX_PARALLEL="${MAX_PARALLEL:-6}"
CPU_THREADS_TOTAL="${CPU_THREADS_TOTAL:-16}"
CPU_THREADS_PER_RUN="${CPU_THREADS_PER_RUN:-$((CPU_THREADS_TOTAL / MAX_PARALLEL))}"
AUTO_SHUTDOWN="${AUTO_SHUTDOWN:-1}"
RESULT_ROOT="$ROOT/results/development/role_gate_phase2ia4"
CONFIG_ROOT="$ROOT/configs/development"

[[ "$MAX_PARALLEL" == "6" ]] || { echo "Phase2IA4 launcher requires MAX_PARALLEL=6 for this launch" >&2; exit 2; }
mkdir -p "$RESULT_ROOT/logs"
GIT_SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo packaged-source)"
sha256_file() { sha256sum "$1" | awk '{print $1}'; }

run_one() {
  local arm="$1" gate_mode="$2" seed="$3"
  local out="$RESULT_ROOT/runs/$arm/seed$seed"
  local log="$RESULT_ROOT/logs/${arm}_seed${seed}.log"
  [[ ! -e "$out" ]] || { echo "Refusing to overwrite existing run: $out" >&2; return 2; }
  local config="$CONFIG_ROOT/phase2ia2_${arm}.json"
  mkdir -p "$out"
  local config_sha
  config_sha="$(sha256_file "$config")"
  "$PYTHON_BIN" -c 'import json,sys; json.dump({"artifact_class":"DEVELOPMENT_ONLY","protocol":"PHASE2IA4","arm":sys.argv[2],"seed":int(sys.argv[3]),"git_sha":sys.argv[4],"config_path":sys.argv[5],"config_sha256":sys.argv[6],"updates":3907,"environment_steps":1000192,"checkpoint":"actor_critic_latest.pt","telemetry":"role_gate_telemetry.csv","resume_allowed":False,"early_stopping_allowed":False,"canonical_data_used":False,"completion_status":"running"},open(sys.argv[1],"w"),indent=2)' "$out/run_manifest.json" "$arm" "$seed" "$GIT_SHA" "$config" "$config_sha"
  (
    export OMP_NUM_THREADS="$CPU_THREADS_PER_RUN"
    export MKL_NUM_THREADS="$CPU_THREADS_PER_RUN"
    export CUDA_DEVICE_MAX_CONNECTIONS=32
    "$PYTHON_BIN" "$ROOT/scripts/train_ri_gmappo.py" --env-name 3d_intercept --target-policy straight --num-envs 4 --rollout-steps 64 --updates 3907 --hidden-dim 64 --role-dim 8 --intent-dim 8 --graph-encoder multi_relation --role-gate-prior-strength 0.4 --multi-relation-global-residual-weight 1.0 --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.30 --message-delay-steps 2 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --disable-evaluation --role-gate-telemetry --save-interval 3907 --device "$DEVICE" --seed "$seed" --role-gate-mode "$gate_mode" --out-dir "$out"
  ) >"$log" 2>&1
  local checkpoint="$out/actor_critic_latest.pt"
  [[ -f "$checkpoint" ]] || { echo "Missing checkpoint: $checkpoint" >&2; return 3; }
  "$PYTHON_BIN" -c 'import hashlib,json,sys; h=hashlib.sha256(); f=open(sys.argv[2],"rb"); [h.update(x) for x in iter(lambda:f.read(1048576),b"")]; f.close(); p=sys.argv[1]; d=json.load(open(p)); d.update({"completion_status":"completed","checkpoint_sha256":h.hexdigest()}); json.dump(d,open(p,"w"),indent=2)' "$out/run_manifest.json" "$checkpoint"
}

# Six independent runs share the 4090; each run keeps the frozen 4-env protocol.
declare -a ARMS=("full_gate:relation_conditioned:101" "full_gate:relation_conditioned:202" "full_gate:relation_conditioned:303" "no_role_gate:none:101" "no_role_gate:none:202" "no_role_gate:none:303")
for ((batch=0; batch<${#ARMS[@]}; batch+=MAX_PARALLEL)); do
  pids=()
  for ((slot=0; slot<MAX_PARALLEL && batch+slot<${#ARMS[@]}; slot++)); do
    IFS=: read -r arm gate_mode seed <<<"${ARMS[batch+slot]}"
    run_one "$arm" "$gate_mode" "$seed" & pids+=("$!")
  done
  failed=0
  for pid in "${pids[@]}"; do
    wait "$pid" || failed=1
  done
  [[ "$failed" == "0" ]] || { echo "A technical run failed; preserving logs and skipping shutdown" >&2; exit 10; }
done

if [[ "$AUTO_SHUTDOWN" == "1" ]]; then
  sync
  shutdown -h now
fi
