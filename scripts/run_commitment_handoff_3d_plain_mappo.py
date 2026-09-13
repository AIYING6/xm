"""Train a development-only plain MAPPO control on commitment-level handoff."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import eval_policy, train_ri_gmappo
from scripts.run_timed_handoff_3d_plain_mappo import build_config, load_agent, parse_args


PROTOCOL = "COMMITMENT-HANDOFF-3D-PLAIN-MAPPO-G2-DEVELOPMENT-V4-RELAY-ACTOR-MASK"


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("pass --execute because this command creates a development run")
    if min(args.updates, args.num_envs, args.rollout_steps, args.selection_eval_episodes, args.endpoint_eval_episodes) <= 0:
        raise ValueError("all training and evaluation counts must be positive")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    args.out_dir.mkdir(parents=True)
    cfg = build_config(args, env_name="commitment_handoff_3d")
    macro_decision_steps = args.updates * args.num_envs * args.rollout_steps
    physical_environment_steps = macro_decision_steps * cfg.handoff_commitment_action_repeat
    manifest = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_G2_LEARNABILITY_PILOT",
        "paper_evidence": False,
        "purpose": "test whether a capacity-controlled plain MAPPO learns the two legal relay commitments without saturation",
        "seed": args.seed,
        "macro_decision_steps": macro_decision_steps,
        "physical_environment_steps": physical_environment_steps,
        # Keep the generic field physically meaningful for downstream budget
        # comparisons; macro decisions remain separately auditable above.
        "environment_steps": physical_environment_steps,
        "task_context_schedule": "balanced deterministic parity across environment seeds",
        "fixed_task": {
            "plant": "original 3DOF UAV dynamics and 27 primitive controls under a fixed legal low-level controller",
            "relay_macro_actions": ["retain_current", "reconstruct_future"],
            "commitment_action_repeat": 8,
            "authorization_window": [12, 28],
            "branch_step": 40,
            "refresh_hold_steps": 16,
            "legacy_intercept_reward_weight": 0.0,
            "service_progress_reward_weight": 1.0,
        },
        "method": "plain capacity-controlled MLP MAPPO; no graph, no sampler, no auxiliary loss",
        "actor_action_contract": {
            "mode": "relay_only",
            "actor_active_agents": ["relay"],
            "critic_observes_all_agents": True,
            "reason": "only the relay macro commitment causally enters the physical controller",
        },
        "status": "running",
    }
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    checkpoint = args.out_dir / "actor_critic_latest.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(f"missing final checkpoint: {checkpoint}")
    endpoint_cfg = build_config(args, env_name="commitment_handoff_3d")
    endpoint_cfg.eval_episodes = args.endpoint_eval_episodes
    endpoint = eval_policy(load_agent(endpoint_cfg, checkpoint), endpoint_cfg, base_seed=740_000)
    row = {"protocol": PROTOCOL, "seed": args.seed, "updates": args.updates, "environment_steps": manifest["environment_steps"], **endpoint}
    with (args.out_dir / "endpoint_evaluation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    manifest.update({"status": "completed", "checkpoint": checkpoint.name, "endpoint": endpoint})
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
