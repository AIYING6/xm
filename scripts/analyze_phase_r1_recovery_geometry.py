"""R1 read-only geometry feasibility analysis; no training or policy results."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


def main() -> None:
    rows = []
    for seed in (1201, 1202, 1203):
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                seed=seed,
                target_policy="straight",
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                relay_dependent_task=True,
                communication_dropout_prob=0.0,
                message_delay_steps=0,
                radar_dropout_prob=0.0,
            )
        )
        env.reset()
        scout, relay, attacker = env.blue_pos
        direct_limit = min(env.config.blue_types[0].comm_range, env.config.blue_types[2].comm_range)
        d_sa = float(np.linalg.norm(scout - attacker))
        d_sr = float(np.linalg.norm(scout - relay))
        d_ra = float(np.linalg.norm(relay - attacker))
        closing_speed = float(env.config.blue_types[0].max_speed + env.config.blue_types[2].max_speed)
        required_distance = max(0.0, d_sa - direct_limit)
        optimistic_steps = required_distance / max(closing_speed, 1e-6)
        rows.append(
            {
                "seed": seed,
                "scout_attacker_initial_distance": d_sa,
                "scout_relay_initial_distance": d_sr,
                "relay_attacker_initial_distance": d_ra,
                "direct_scout_attacker_comm_limit": direct_limit,
                "initial_direct_link": d_sa <= direct_limit,
                "required_closing_distance": required_distance,
                "optimistic_closing_steps": optimistic_steps,
                "failure_step": 44,
                "failure_duration_steps": 80,
                "remaining_horizon_after_failure": 216,
                "time_margin_steps": 216 - optimistic_steps,
                "geometrically_time_reachable": optimistic_steps < 216,
            }
        )
    payload = {
        "protocol": "PHASE-R1-GEOMETRY-V1",
        "artifact_class": "READ_ONLY_GEOMETRY_FEASIBILITY",
        "canonical_data_used": False,
        "training_started": False,
        "rows": rows,
        "pass": all(row["geometrically_time_reachable"] and not row["initial_direct_link"] for row in rows),
    }
    print(json.dumps(payload, indent=2))
    if not payload["pass"]:
        raise SystemExit("R1 geometry feasibility failed")


if __name__ == "__main__":
    main()
