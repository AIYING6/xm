"""Method-independent packet-loss calibration for the L3 progression."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from scripts.run_l2_limited_communication_development import cfg
from scripts import run_new_project_l0_single_interceptor as l0

OUT = Path("results/l3_packet_loss_calibration")
SEEDS = tuple(range(860_000, 860_008))
PROBS = (0.1, 0.3, 0.5, 0.7)


def measure(prob: float) -> dict:
    ratios, streaks, ages = [], [], []
    for seed in SEEDS:
        run_cfg = cfg(8501, OUT / "template", updates=1)
        run_cfg.communication_dropout_prob = prob
        env = l0.make_env(run_cfg, seed, training=False)
        obs, share, graph = env.reset()
        rng = np.random.default_rng(seed + 19)
        streak = 0
        while True:
            action = np.column_stack((rng.uniform(-1, 1, env.config.num_blue), rng.uniform(-1, 1, env.config.num_blue), rng.choice([-1., 1.], env.config.num_blue))).astype(np.float32)
            obs, share, graph, _r, dones, _info = env.step(action)
            adj = np.asarray(env.comm_adj, dtype=np.float32)
            ratio = float((adj.sum() - env.config.num_blue) / max(1, env.config.num_blue * (env.config.num_blue - 1)))
            ratios.append(ratio)
            streak = streak + 1 if ratio == 0.0 else 0
            streaks.append(streak)
            for cache in env.sender_packet_cache:
                for packet in cache.values():
                    ages.append(max(0, env.step_count - int(packet.get("send_step", env.step_count))))
            if bool(np.all(dones)):
                break
    return {"prob": prob, "mean_delivery_ratio": float(np.mean(ratios)), "p95_no_delivery_streak": float(np.percentile(streaks, 95)), "mean_cache_age": float(np.mean(ages)) if ages else 0.0}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [measure(p) for p in PROBS]
    payload = {"status": "L3_PACKET_LOSS_CALIBRATION_COMPLETE", "seeds": list(SEEDS), "rows": rows, "selected_prob": 0.3, "selection_rule": "intermediate delivery degradation, not near-total outage"}
    (OUT / "L3_PACKET_LOSS_CALIBRATION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
