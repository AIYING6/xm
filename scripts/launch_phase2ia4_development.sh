#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
DEVICE="${DEVICE:-cuda}"
RESULT_ROOT="$ROOT/results/development/role_gate_phase2ia4"
CONFIG_ROOT="$ROOT/configs/development"
mkdir -p "$RESULT_ROOT"
GIT_SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo packaged-source)"
sha256_file() { sha256sum "$1" | awk '{print $1}'; }
for arm_mode in "full_gate:relation_conditioned" "no_role_gate:none"; do
  arm="${arm_mode%%:*}"; gate_mode="${arm_mode##*:}"
  for seed in 101 202 303; do
    out="$RESULT_ROOT/runs/$arm/seed$seed"
    [[ ! -e "$out" ]] || { echo "Refusing to overwrite existing run: $out" >&2; exit 2; }
    config="$CONFIG_ROOT/phase2ia2_${arm}.json"
    mkdir -p "$out"
    config_sha="$(sha256_file "$config")"
    "$PYTHON_BIN" -c 'import json,sys; json.dump({"artifact_class":"DEVELOPMENT_ONLY","protocol":"PHASE2IA4","arm":sys.argv[2],"seed":int(sys.argv[3]),"git_sha":sys.argv[4],"config_path":sys.argv[5],"config_sha256":sys.argv[6],"updates":3907,"environment_steps":1000192,"checkpoint":"actor_critic_latest.pt","telemetry":"role_gate_telemetry.csv","resume_allowed":False,"early_stopping_allowed":False,"canonical_data_used":False,"completion_status":"running"},open(sys.argv[1],"w"),indent=2)' "$out/run_manifest.json" "$arm" "$seed" "$GIT_SHA" "$config" "$config_sha"
    "$PYTHON_BIN" "$ROOT/scripts/train_ri_gmappo.py" --env-name 3d_intercept --target-policy straight --num-envs 4 --rollout-steps 64 --updates 3907 --hidden-dim 64 --role-dim 8 --intent-dim 8 --graph-encoder multi_relation --role-gate-prior-strength 0.4 --multi-relation-global-residual-weight 1.0 --strict-target-sensing --agent-target-info-bottleneck --communication-dropout-prob 0.30 --message-delay-steps 2 --failed-blue-agent 1 --node-failure-start-step 40 --node-failure-duration-steps 80 --disable-evaluation --role-gate-telemetry --save-interval 3907 --device "$DEVICE" --seed "$seed" --role-gate-mode "$gate_mode" --out-dir "$out"
    checkpoint="$out/actor_critic_latest.pt"
    [[ -f "$checkpoint" ]] || { echo "Missing checkpoint: $checkpoint" >&2; exit 3; }
    "$PYTHON_BIN" -c 'import hashlib,json,sys; h=hashlib.sha256(); f=open(sys.argv[2],"rb"); [h.update(x) for x in iter(lambda:f.read(1048576),b"")]; f.close(); p=sys.argv[1]; d=json.load(open(p)); d.update({"completion_status":"completed","checkpoint_sha256":h.hexdigest()}); json.dump(d,open(p,"w"),indent=2)' "$out/run_manifest.json" "$checkpoint"
  done
done
