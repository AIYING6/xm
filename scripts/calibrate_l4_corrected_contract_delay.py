"""Read-only L4 delay-mechanics confirmation under the repaired actor contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_l3_corrected_contract_requalification as l3r
from scripts import run_new_project_l0_single_interceptor as l0


OUT = ROOT / "results" / "l4_corrected_contract_delay_calibration"
SEEDS = tuple(range(880_000, 880_008))
DELAY_STEPS = 8


def measure() -> dict:
    """Measure delivered/cache-valid ages only; no learned policy is used."""
    delivered_ages, valid_ages, no_fresh_streaks = [], [], []
    for seed in SEEDS:
        config = l3r.cfg(8701, OUT / "template", updates=1)
        config.message_delay_steps = DELAY_STEPS
        env = l0.make_env(config, seed, training=False)
        obs, share, graph = env.reset()
        rng = np.random.default_rng(seed + 29)
        no_fresh = 0
        while True:
            action = np.column_stack(
                (
                    rng.uniform(-1, 1, env.config.num_blue),
                    rng.uniform(-1, 1, env.config.num_blue),
                    rng.choice([-1.0, 1.0], env.config.num_blue),
                )
            ).astype(np.float32)
            obs, share, graph, _reward, dones, _info = env.step(action)
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
        "message_delay_steps": DELAY_STEPS,
        "mean_delivered_message_age": float(np.mean(delivered_ages)) if delivered_ages else 0.0,
        "p95_delivered_message_age": float(np.percentile(delivered_ages, 95)) if delivered_ages else 0.0,
        "mean_cache_valid_age": float(np.mean(valid_ages)) if valid_ages else 0.0,
        "p95_no_fresh_message_streak": float(np.percentile(no_fresh_streaks, 95)),
        "cache_valid_record_count": len(valid_ages),
    }


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite calibration output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "L4_CORRECTED_CONTRACT_DELAY_MECHANICS_CONFIRMED",
        "performance_use_prohibited": True,
        "seeds": list(SEEDS),
        "strict_target_contract": True,
        "selection": "delay 8 retained; no retuning or severity search",
        "metrics": measure(),
    }
    (OUT / "L4_CORRECTED_CONTRACT_DELAY_CALIBRATION.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
