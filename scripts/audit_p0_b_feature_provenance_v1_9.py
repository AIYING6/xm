"""Deterministic P0-B provenance counterexample for the frozen PCRF-R2 contract.

This is an audit, not a repair.  It demonstrates whether a target claim whose
generation time is older than ``max_target_message_age_steps`` can still enter
the R2 C branch through a delivered sender-status packet.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


def test_expired_delivered_target_claim_enters_c_branch() -> None:
    """Confirm the contract deviation without changing any protocol setting."""
    cfg = UAVIntercept3DConfig(
        seed=59,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        communication_dropout_prob=0.0,
        max_target_message_age_steps=2,
    )
    env = UAVIntercept3DEnv(cfg)
    _, _, _ = env.reset()

    receiver, sender = 0, 1
    packet = copy.deepcopy(env.sender_packet_cache[receiver][sender])
    packet.update(
        {
            "validity": 1.0,
            "target_pos": np.asarray([1_234.0, -567.0, 4_321.0], dtype=np.float32),
            "target_vel": np.asarray([10.0, -5.0, 1.0], dtype=np.float32),
            "target_confidence": 1.0,
            "target_generation_step": 0,
            "send_step": 0,
            "delivery_step": 0,
        }
    )
    env.sender_packet_cache[receiver][sender] = packet
    env.step_count = cfg.max_target_message_age_steps + 1

    graph = env._get_graph_obs()
    target_index = graph["pcrf_r2_c_node_feat"].shape[1] - 1
    c_target_available = float(graph["pcrf_r2_c_adj"][receiver, 0, target_index])
    c_target_x = float(graph["pcrf_r2_c_node_feat"][receiver, target_index, 0])
    assert c_target_available == 1.0
    assert c_target_x != 0.0
    assert env.step_count - packet["target_generation_step"] > cfg.max_target_message_age_steps
    print(
        "P0_B_FEATURE_PROVENANCE_COUNTEREXAMPLE_CONFIRMED "
        f"age={env.step_count - packet['target_generation_step']} "
        f"max_age={cfg.max_target_message_age_steps} "
        f"c_target_available={c_target_available}"
    )


def main() -> None:
    test_expired_delivered_target_claim_enters_c_branch()
    print("P0_B_FEATURE_PROVENANCE_AUDIT_V1_9: CONTRACT_DEVIATION_CONFIRMED")


if __name__ == "__main__":
    main()
