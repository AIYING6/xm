"""Method-independent message-delay calibration for the L4 progression."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scripts import run_new_project_l0_single_interceptor as l0
from scripts.run_l3_packet_loss_development import cfg


OUT = Path("results/l4_delay_calibration")
SEEDS = tuple(range(880_000, 880_008))
CANDIDATE_DELAYS = (2, 4, 8, 16)


def _measure(delay: int) -> dict:
    delivered_ages, valid_ages, no_fresh_streaks = [], [], []
    for seed in SEEDS:
        run_cfg = cfg(8701, OUT / "template", updates=1)
        run_cfg.message_delay_steps = delay
        env = l0.make_env(run_cfg, seed, training=False)
        _obs, _share, _graph = env.reset()
        rng = np.random.default_rng(seed + 29)
        no_fresh = 0
        while True:
            action = np.column_stack((
                rng.uniform(-1, 1, env.config.num_blue),
                rng.uniform(-1, 1, env.config.num_blue),
                rng.choice([-1.0, 1.0], env.config.num_blue),
            )).astype(np.float32)
            _obs, _share, _graph, _reward, dones, _info = env.step(action)
            fresh = False
            for cache in env.sender_packet_cache:
                for packet in cache.values():
                    age = max(0, env.step_count - int(packet.get("send_step", env.step_count)))
                    delivered_ages.append(age)
                    if age <= env.config.max_target_message_age_steps:
                        valid_ages.append(age)
                        fresh = True
            no_fresh = 0 if fresh else no_fresh + 1
            no_fresh_streaks.append(no_fresh)
            if bool(np.all(dones)):
                break
    return {
        "delay_steps": delay,
        "mean_delivered_message_age": float(np.mean(delivered_ages)) if delivered_ages else 0.0,
        "p95_delivered_message_age": float(np.percentile(delivered_ages, 95)) if delivered_ages else 0.0,
        "mean_cache_valid_age": float(np.mean(valid_ages)) if valid_ages else 0.0,
        "p95_no_fresh_message_streak": float(np.percentile(no_fresh_streaks, 95)),
        "cache_valid_record_count": len(valid_ages),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [_measure(delay) for delay in CANDIDATE_DELAYS]
    payload = {
        "status": "L4_DELAY_CALIBRATION_COMPLETE",
        "seeds": list(SEEDS),
        "rows": rows,
        "selected_delay_steps": 8,
        "selection_rule": "nontrivial message age and fresh-message gaps while cache-valid evidence remains common",
    }
    (OUT / "L4_DELAY_CALIBRATION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
