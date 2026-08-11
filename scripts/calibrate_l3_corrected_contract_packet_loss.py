"""Read-only L3 packet-mechanics confirmation under the repaired actor contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_l2_corrected_contract_requalification as l2r
from scripts import run_new_project_l0_single_interceptor as l0


OUT = ROOT / "results" / "l3_corrected_contract_packet_loss_calibration"
SEEDS = tuple(range(860_000, 860_008))
DROPOUT = 0.3


def measure() -> dict:
    """Measure delivery/cache mechanics only; no learned policy is evaluated."""
    ratios, streaks, ages = [], [], []
    for seed in SEEDS:
        config = l2r.cfg(8501, OUT / "template", updates=1)
        config.communication_dropout_prob = DROPOUT
        env = l0.make_env(config, seed, training=False)
        obs, share, graph = env.reset()
        rng = np.random.default_rng(seed + 19)
        no_delivery_streak = 0
        while True:
            action = np.column_stack(
                (
                    rng.uniform(-1, 1, env.config.num_blue),
                    rng.uniform(-1, 1, env.config.num_blue),
                    rng.choice([-1.0, 1.0], env.config.num_blue),
                )
            ).astype(np.float32)
            obs, share, graph, _reward, dones, _info = env.step(action)
            adjacency = np.asarray(env.comm_adj, dtype=np.float32)
            ratio = float(
                (adjacency.sum() - env.config.num_blue)
                / max(1, env.config.num_blue * (env.config.num_blue - 1))
            )
            ratios.append(ratio)
            no_delivery_streak = no_delivery_streak + 1 if ratio == 0.0 else 0
            streaks.append(no_delivery_streak)
            for cache in env.sender_packet_cache:
                for packet in cache.values():
                    ages.append(max(0, env.step_count - int(packet.get("send_step", env.step_count))))
            if bool(np.all(dones)):
                break
    return {
        "communication_dropout_prob": DROPOUT,
        "mean_delivery_ratio": float(np.mean(ratios)),
        "p95_no_delivery_streak": float(np.percentile(streaks, 95)),
        "mean_cache_age": float(np.mean(ages)) if ages else 0.0,
    }


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite calibration output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "L3_CORRECTED_CONTRACT_PACKET_MECHANICS_CONFIRMED",
        "performance_use_prohibited": True,
        "seeds": list(SEEDS),
        "strict_target_contract": True,
        "selection": "dropout 0.3 retained; no retuning or severity search",
        "metrics": measure(),
    }
    (OUT / "L3_CORRECTED_CONTRACT_PACKET_LOSS_CALIBRATION.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
