"""Deterministic R1 tests for the v1.6R legal information boundary."""
from __future__ import annotations

import copy
import numpy as np

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv
from envs.v16r_legal_interface import LegalObservationInterface, stack_recipient_graphs


def main() -> int:
    cfg = UAVIntercept3DConfig(seed=17061, strict_target_sensing=True, agent_target_info_bottleneck=True)
    env = UAVIntercept3DEnv(cfg)
    legal = LegalObservationInterface(env)
    failures: list[str] = []

    # Force a no-evidence state, then prove global target changes are invisible.
    env.detected_by[:] = 0.0
    env.target_cache_valid[:] = 0.0
    env.target_cache_generation_step[:] = -1
    env.last_detected_target_pos = np.asarray([9999.0, 9999.0, 9999.0], dtype=np.float32)
    a = legal.snapshot(1)
    env.red_pos[0] += np.asarray([1234.0, -567.0, 89.0], dtype=np.float32)
    env.last_detected_target_pos = np.asarray([-7777.0, 3333.0, 1111.0], dtype=np.float32)
    b = legal.snapshot(1)
    if a["target_evidence"].available or b["target_evidence"].available:
        failures.append("no-evidence state became available")
    if not np.array_equal(a["target_evidence"].position, b["target_evidence"].position):
        failures.append("global target changed actor evidence")

    # Local sensing is legal and should update the recipient only.
    env.detected_by[:] = 0.0
    env.detected_by[0] = 1.0
    local = legal.target_evidence(0)
    if not local.available or local.kind != "local_sensing":
        failures.append("local sensing was not exposed")

    # Delivered cache is legal; expired cache is not.
    env.detected_by[:] = 0.0
    env.target_cache_valid[1] = 1.0
    env.target_cache_pos[1] = np.asarray([1.0, 2.0, 3.0], dtype=np.float32)
    env.target_cache_vel[1] = np.asarray([4.0, 0.0, 0.0], dtype=np.float32)
    env.target_cache_generation_step[1] = env.step_count
    env.target_cache_confidence[1] = 1.0
    env.target_cache_source[1] = 0
    env.target_cache_path[1] = [0, 1]
    cached = legal.target_evidence(1)
    if not cached.available or cached.kind != "delivered_cache" or cached.source != 0:
        failures.append("valid delivered cache was not exposed")
    env.target_cache_generation_step[1] = env.step_count - cfg.max_target_message_age_steps - 1
    expired = legal.target_evidence(1)
    if expired.available:
        failures.append("expired cache was exposed")

    # Evidence is recipient-specific: a cache held by agent 0 cannot appear
    # in agent 1's view.
    env.target_cache_valid[1] = 0.0
    env.target_cache_valid[0] = 1.0
    env.target_cache_generation_step[0] = env.step_count
    env.target_cache_confidence[0] = 1.0
    env.target_cache_source[0] = 0
    if legal.target_evidence(1).available:
        failures.append("recipient-0 cache leaked to recipient 1")

    # A legal local sensing event is private to the sensing recipient.
    env.target_cache_valid[:] = 0.0
    env.detected_by[:] = 0.0
    env.detected_by[0] = 1.0
    if legal.target_evidence(1).available:
        failures.append("recipient-0 sensing leaked to recipient 1")

    graph = legal.recipient_graph(1)
    if graph["relation_adj"].shape != (2, cfg.num_blue + cfg.num_red, cfg.num_blue + cfg.num_red):
        failures.append("recipient graph shape mismatch")
    if not np.isfinite(graph["node"]).all() or not np.isfinite(graph["edge"]).all():
        failures.append("graph contains non-finite values")
    stacked = stack_recipient_graphs(legal)
    if stacked["node"].shape[0] != cfg.num_blue:
        failures.append("recipient graph stack lacks recipient dimension")
    if stacked["relation_adj"].shape[1] != 2:
        failures.append("recipient graph relation dimension mismatch")

    print(f"checks={11}, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
