"""One-update compatibility smoke for S1's opt-in RNG decomposition."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo


def run(mode: str, seed: int) -> dict:
    out = Path("results/development/drtp_seed_s1_compatibility_smoke") / mode / f"seed{seed}"
    cfg = RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=seed,
        num_envs=4,
        rollout_steps=64,
        updates=1,
        hidden_dim=115,
        graph_encoder="single",
        device="cuda" if __import__("torch").cuda.is_available() else "cpu",
        evaluation_enabled=False,
        drtp_sampler_mode=mode,
        drtp_sampler_seed=seed,
        drtp_sampler_total_updates=1,
        drtp_sampler_logging=True,
        out_dir=str(out),
        save_interval=1,
        rng_decomposition=True,
    )
    train_ri_gmappo(cfg)
    manifest = {"mode": mode, "seed": seed, "status": "completed", "out_dir": str(out)}
    (out / "s1_compatibility_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    results = [run("utr", 1901), run("drtp", 1901)]
    print(json.dumps({"status": "PASS", "runs": results}, indent=2))


if __name__ == "__main__":
    main()

