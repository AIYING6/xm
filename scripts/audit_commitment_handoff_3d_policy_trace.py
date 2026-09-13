"""Read-only behavior trace for a commitment-handoff checkpoint.

The trace separates a policy that cannot produce a valid service trajectory
from one that reaches the route but ignores the public mission context.  It
does not train, alter a checkpoint, or make a method comparison.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import make_env, stack_graphs
from envs.timed_handoff_intercept_3d_env import HANDOFF_CONTEXTS
from scripts.run_timed_handoff_3d_plain_mappo import build_config, load_agent


PROTOCOL = "COMMITMENT-HANDOFF-3D-READONLY-POLICY-TRACE-V1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--episodes-per-context", type=int, default=20)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def phase(step: int, authorization_start: int, authorization_deadline: int, branch_step: int) -> str:
    if step < authorization_start:
        return "pre_authorization"
    if step <= authorization_deadline:
        return "authorization"
    if step >= branch_step:
        return "postbranch"
    return "between_stages"


def mean_or_zero(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("pass --execute because this command writes a development diagnostic")
    if not args.checkpoint.is_file():
        raise FileNotFoundError(args.checkpoint)
    if args.episodes_per_context <= 0:
        raise ValueError("episodes-per-context must be positive")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    requested_out_dir = args.out_dir

    # These fields are required only to reuse the common runner config.
    args.updates = 1
    args.num_envs = 1
    args.rollout_steps = 1
    args.selection_eval_episodes = 1
    args.endpoint_eval_episodes = args.episodes_per_context
    args.out_dir = Path("unused")
    cfg = build_config(args, env_name="commitment_handoff_3d")
    cfg.timed_handoff_context_mode = "balanced"
    agent = load_agent(cfg, args.checkpoint)
    device = torch.device(cfg.device)
    rows: list[dict[str, object]] = []

    agent.eval()
    with torch.no_grad():
        for context_index, context in enumerate(HANDOFF_CONTEXTS):
            for episode in range(args.episodes_per_context):
                env_cfg = build_config(args, env_name="commitment_handoff_3d")
                env_cfg.timed_handoff_context_mode = context
                env = make_env(env_cfg, 760_000 + context_index * 10_000 + episode, training=False)
                obs, share_obs, graph = env.reset()
                phase_actions = {name: [] for name in ("pre_authorization", "authorization", "between_stages", "postbranch")}
                info: dict[str, object] = {}
                while True:
                    packed = stack_graphs([graph])
                    actions, *_ = agent.get_action_and_value(
                        torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                        torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(packed["role"], dtype=torch.long, device=device),
                        torch.as_tensor(packed["adj"], dtype=torch.float32, device=device),
                        torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                        relation_adj=torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device),
                        deterministic=True,
                    )
                    macro = actions.squeeze(0).cpu().numpy()
                    stage = phase(
                        int(env.step_count),
                        int(env.handoff_config.authorization_start_step),
                        int(env.handoff_config.authorization_deadline),
                        int(env.handoff_config.branch_step),
                    )
                    phase_actions[stage].append(float(macro[1] == 1))
                    obs, share_obs, graph, _, dones, info = env.step(macro)
                    if bool(np.all(dones)):
                        rows.append(
                            {
                                "context": context,
                                "episode": episode,
                                "success": float(info.get("success", 0.0)),
                                "timeout": float(info.get("timeout", 0.0)),
                                "collision": float(info.get("collision", 0.0)),
                                "terminal_service_progress": float(info.get("handoff_service_progress", 0.0)),
                                **{f"reconstruct_fraction_{name}": mean_or_zero(values) for name, values in phase_actions.items()},
                            }
                        )
                        break

    summary: dict[str, dict[str, float]] = {}
    action_fields = [field for field in rows[0] if field.startswith("reconstruct_fraction_")]
    for context in HANDOFF_CONTEXTS:
        cell = [row for row in rows if row["context"] == context]
        summary[context] = {
            "success_rate": mean_or_zero([float(row["success"]) for row in cell]),
            "timeout_rate": mean_or_zero([float(row["timeout"]) for row in cell]),
            **{field: mean_or_zero([float(row[field]) for row in cell]) for field in action_fields},
        }
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_READONLY_POLICY_DIAGNOSTIC",
        "training_started": False,
        "checkpoint": str(args.checkpoint),
        "seed": args.seed,
        "summary": summary,
        "interpretation": (
            "Action fractions describe the fixed policy's legal relay commitments; "
            "they do not establish why learning succeeded or failed."
        ),
    }
    requested_out_dir.mkdir(parents=True)
    with (requested_out_dir / "policy_trace_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (requested_out_dir / "policy_trace_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
