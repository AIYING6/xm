"""Read-only P0 provenance audit for Phase2IB task semantics."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


def main() -> None:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=21803,
            target_policy="straight",
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            relay_dependent_task=True,
            failed_blue_agent=1,
            node_failure_start_step=5,
            node_failure_duration_steps=10,
            communication_dropout_prob=0.0,
            radar_dropout_prob=0.0,
        )
    )
    env.reset()
    env._write_target_cache(
        2,
        pos=env.red_pos[0], vel=env.red_pos[0] * 0.0, source=0,
        generation_step=0, delivery_step=0, hop_count=2, confidence=1.0,
        path=[0, 1, 2],
    )
    before = env._has_target_information(2)
    env.step_count = 5
    during = env._has_target_information(2)
    env.step_count = 15
    after = env._has_target_information(2)
    payload = {
        "protocol": "PHASE2IB-RDT-V1",
        "artifact_class": "P0_SEMANTIC_AUDIT",
        "training_started": False,
        "canonical_data_used": False,
        "attacker_cache_path": env.target_cache_path[2],
        "attacker_information_before_failure": before,
        "attacker_information_during_relay_failure": during,
        "attacker_information_after_relay_failure": after,
        "pass": before is True and during is False and after is True,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["pass"]:
        raise SystemExit("P0 audit failed")


if __name__ == "__main__":
    main()
