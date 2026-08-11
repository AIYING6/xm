"""Method-independent relay-failure onset calibration for L5."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR, ROLE_RELAY
from scripts import run_new_project_l0_single_interceptor as l0
from scripts.run_l4_delay_development import _continuous_from_legacy, cfg


OUT = Path("results/l5_relay_failure_calibration_v2")
SEEDS = tuple(range(900_000, 900_008))
ONSETS = (20, 40, 60, 80)
HORIZON = 180


def _trial(onset: int, seed: int) -> dict:
    run_cfg = cfg(8901, OUT / "template", updates=1)
    env = l0.make_env(run_cfg, seed, training=False)
    relay_id = next(i for i, typ in enumerate(env.config.blue_types) if typ.role == ROLE_RELAY)
    env.config.failed_blue_agent = relay_id
    env.config.node_failure_start_step = onset
    env.config.node_failure_duration_steps = HORIZON
    obs, _share, _graph = env.reset()
    attacker_ids = [i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}]
    pre, post, failed_steps = [], [], 0
    relay_cache_ages_pre, relay_cache_ages_post = [], []
    while True:
        legacy = np.zeros(env.config.num_blue, dtype=np.int64)
        for i in attacker_ids:
            legacy[i] = int(l0.heuristic_action(obs[i:i + 1])[0])
        action = _continuous_from_legacy(env, legacy, already_guidance=True)
        for i, typ in enumerate(env.config.blue_types):
            if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
                action[i, 2] = -1.0
        obs, _share, _graph, _reward, dones, info = env.step(action)
        links = float((env.comm_adj.sum() - env.config.num_blue) / max(1, env.config.num_blue * (env.config.num_blue - 1)))
        relay_ages = []
        for receiver, cache in enumerate(env.sender_packet_cache):
            if receiver == relay_id:
                continue
            packet = cache.get(relay_id)
            if packet is not None and float(packet.get("validity", 0.0)) > 0.5:
                relay_ages.append(max(0, env.step_count - int(packet.get("send_step", env.step_count))))
        if env.step_count < onset:
            pre.append(links)
            relay_cache_ages_pre.extend(relay_ages)
        else:
            post.append(links)
            relay_cache_ages_post.extend(relay_ages)
            failed_steps += int(info.get("node_failure_active", 0.0) > 0.5)
        if bool(np.all(dones)):
            return {"onset": onset, "episode_seed": seed, "final_outcome": l0.outcome(info),
                    "termination_step": int(info["step"]), "pre_failure_link_rate": float(np.mean(pre)) if pre else 0.0,
                    "post_failure_link_rate": float(np.mean(post)) if post else 0.0,
                    "pre_relay_cache_age": float(np.mean(relay_cache_ages_pre)) if relay_cache_ages_pre else None,
                    "post_relay_cache_age": float(np.mean(relay_cache_ages_post)) if relay_cache_ages_post else None,
                    "failure_active_steps": failed_steps}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [_trial(onset, seed) for onset in ONSETS for seed in SEEDS]
    summary = []
    for onset in ONSETS:
        group = [r for r in rows if r["onset"] == onset]
        summary.append({"onset": onset,
                        "scripted_neutralization_rate": float(np.mean([r["final_outcome"] == "NEUTRALIZED" for r in group])),
                        "mean_termination_step": float(np.mean([r["termination_step"] for r in group])),
                        "mean_pre_failure_link_rate": float(np.mean([r["pre_failure_link_rate"] for r in group])),
                        "mean_post_failure_link_rate": float(np.mean([r["post_failure_link_rate"] for r in group])),
                        "mean_pre_relay_cache_age": float(np.mean([r["pre_relay_cache_age"] for r in group if r["pre_relay_cache_age"] is not None])) if any(r["pre_relay_cache_age"] is not None for r in group) else None,
                        "mean_post_relay_cache_age": float(np.mean([r["post_relay_cache_age"] for r in group if r["post_relay_cache_age"] is not None])) if any(r["post_relay_cache_age"] is not None for r in group) else None,
                        "mean_failure_active_steps": float(np.mean([r["failure_active_steps"] for r in group]))})
    payload = {"status": "L5_RELAY_FAILURE_CALIBRATION_COMPLETE", "seeds": list(SEEDS), "summary": summary,
               "selected_onset": 40, "selected_duration_steps": HORIZON,
               "selection_rule": "topology changes before typical scripted neutralization while scripted task space remains partially reachable"}
    (OUT / "L5_RELAY_FAILURE_CALIBRATION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
