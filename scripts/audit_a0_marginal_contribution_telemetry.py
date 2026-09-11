"""Read-only non-degeneracy audit of A0 marginal-observability telemetry."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.m2_commitment_ppo import M2PlainMAPPO
from envs.active_perception_tracking_env import ActivePerceptionTrackingEnv
from envs.observability_active_perception import marginal_bearing_contributions
from scripts.run_a0_plain_mappo_pilot import PROTOCOL, choose


def load_agent(path: Path) -> M2PlainMAPPO:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL:
        raise ValueError(f"unexpected endpoint protocol: {path}")
    agent = M2PlainMAPPO(obs_dim=10, critic_dim=13, hidden_dim=96, action_dim=5)
    agent.load_state_dict(payload["state_dict"]); agent.eval()
    return agent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoints", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to run without --execute")
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = []
    for checkpoint in args.checkpoints:
        agent = load_agent(checkpoint)
        contributions = []
        active_count = 0
        for episode in range(16):
            env = ActivePerceptionTrackingEnv(seed=50_000 + episode)
            env.reset()
            while not env.done:
                values = marginal_bearing_contributions(
                    env.belief_covariance, env.belief_mean, env.uav_positions,
                    [item.sensing_range for item in env.uav_types],
                    [item.bearing_variance for item in env.uav_types],
                )
                contributions.extend(values.tolist())
                active_count += int(np.count_nonzero(values > 1e-10))
                env.step(choose(agent, env))
        values = np.asarray(contributions, dtype=np.float64)
        rows.append({
            "checkpoint": str(checkpoint),
            "samples": int(values.size),
            "positive_fraction": float(np.mean(values > 1e-10)),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "active_samples": active_count,
        })
    checks = {
        "every_seed_has_legal_nonzero_contributions": all(row["positive_fraction"] > 0.0 for row in rows),
        "every_seed_has_temporal_or_agent_variation": all(row["std"] > 1e-10 for row in rows),
        "pooled_signal_not_constant": float(np.std([row["mean"] for row in rows] + [row["std"] for row in rows])) > 1e-10,
    }
    payload = {
        "protocol": "A0-MARGINAL-OBSERVABILITY-TELEMETRY-AUDIT-V1",
        "verdict": "A0_MARGINAL_TELEMETRY_NONDEGENERATE" if all(checks.values()) else "A0_MARGINAL_TELEMETRY_DEGENERATE",
        "training_started": False,
        "method_training_started": False,
        "rows": rows,
        "checks": checks,
        "interpretation": "This audit only establishes whether the proposed public-belief marginal signal is nonzero and variable along fixed baseline trajectories. It does not establish a causal mechanism or an OC-MAPPO performance advantage.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
