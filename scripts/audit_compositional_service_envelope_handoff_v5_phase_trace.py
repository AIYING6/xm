"""Read-only phase trace for a fixed V5 service-envelope checkpoint.

The trace distinguishes a policy that recognizes ``future`` only as a static
label from one that preserves the current service before the public branch and
reconstructs after it.  It never trains or changes a checkpoint.
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

from algorithms.ri_gmappo.simple_ri_gmappo import make_env, stack_graphs  # noqa: E402
from scripts.run_compositional_service_envelope_handoff_plain_mappo import build_config, load_agent  # noqa: E402


PROTOCOL = "COMMITMENT-HANDOFF-3D-V5-READONLY-PHASE-TRACE-V1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--service-envelope-mode", default="compositional_v5")
    parser.add_argument("--future-corridor-lateral-offset", type=float, default=1_500.0)
    parser.add_argument("--branch-step", type=int, default=40)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def phase(step: int, branch_step: int) -> str:
    return "prebranch" if step < branch_step else "postbranch"


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("pass --execute because this writes a development-only trace")
    if not args.checkpoint.is_file():
        raise FileNotFoundError(args.checkpoint)
    if args.episodes <= 0 or args.out_dir.exists():
        raise ValueError("episodes must be positive and out-dir must not already exist")
    # Reuse the frozen runner configuration; only the read-only profile and
    # checkpoint differ from its training construction.
    args.updates = args.num_envs = args.rollout_steps = args.selection_eval_episodes = 1
    args.endpoint_episodes_per_profile = 1
    agent = load_agent(build_config(args), args.checkpoint)
    device = torch.device(args.device)
    macro_rows: list[dict[str, object]] = []
    episode_rows: list[dict[str, object]] = []
    with torch.no_grad():
        for episode in range(args.episodes):
            cfg = build_config(args, profile=args.profile)
            env = make_env(cfg, 860_000 + episode, training=False)
            obs, share_obs, graph = env.reset()
            action_by_phase: dict[str, list[float]] = {"prebranch": [], "postbranch": []}
            info: dict[str, object] = {}
            while True:
                packed = stack_graphs([graph])
                action, *_ = agent.get_action_and_value(
                    torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                    torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(packed["role"], dtype=torch.long, device=device),
                    torch.as_tensor(packed["adj"], dtype=torch.float32, device=device),
                    torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                    relation_adj=torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device),
                    deterministic=True,
                )
                macro = action.squeeze(0).cpu().numpy()
                start_step = int(env.step_count)
                current_phase = phase(start_step, int(env.handoff_config.branch_step))
                reconstruct = float(macro[1] == 1)
                action_by_phase[current_phase].append(reconstruct)
                obs, share_obs, graph, _, dones, info = env.step(macro)
                macro_rows.append({
                    "episode": episode,
                    "profile": args.profile,
                    "phase": current_phase,
                    "start_step": start_step,
                    "end_step": int(env.step_count),
                    "relay_reconstruct": reconstruct,
                    "relay_current_corridor_error": float(info.get("relay_current_corridor_error", np.nan)),
                    "relay_future_corridor_error": float(info.get("relay_future_corridor_error", np.nan)),
                })
                if bool(np.all(dones)):
                    episode_rows.append({
                        "episode": episode,
                        "profile": args.profile,
                        "success": float(info.get("success", 0.0)),
                        "timeout": float(info.get("timeout", 0.0)),
                        "collision": float(info.get("collision", 0.0)),
                        "prebranch_reconstruct_fraction": float(np.mean(action_by_phase["prebranch"])) if action_by_phase["prebranch"] else 0.0,
                        "postbranch_reconstruct_fraction": float(np.mean(action_by_phase["postbranch"])) if action_by_phase["postbranch"] else 0.0,
                    })
                    break
    args.out_dir.mkdir(parents=True)
    for name, rows in (("macro_phase_trace.csv", macro_rows), ("episode_phase_summary.csv", episode_rows)):
        with (args.out_dir / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_READONLY_BEHAVIOR_DIAGNOSTIC",
        "training_started": False,
        "checkpoint": str(args.checkpoint),
        "profile": args.profile,
        "episodes": args.episodes,
        "summary": {
            "success_rate": float(np.mean([row["success"] for row in episode_rows])),
            "mean_prebranch_reconstruct_fraction": float(np.mean([row["prebranch_reconstruct_fraction"] for row in episode_rows])),
            "mean_postbranch_reconstruct_fraction": float(np.mean([row["postbranch_reconstruct_fraction"] for row in episode_rows])),
        },
        "interpretation": "The trace describes a fixed policy; it cannot by itself identify a learning mechanism.",
    }
    (args.out_dir / "phase_trace_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
