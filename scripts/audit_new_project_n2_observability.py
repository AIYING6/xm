"""Read-only N2 observability diagnostic after a learnability NO-GO.

This audit never reads target truth.  It measures only non-zero target-relative
fields already exposed to each recipient actor by the frozen N1 contract.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import make_env  # noqa: E402
from scripts.run_new_project_n2_development_pilot import (  # noqa: E402
    EVAL_SEEDS,
    mission_cfg,
    random_no_commit,
    scripted_legal_heuristic,
)


def main() -> None:
    output = ROOT / "results" / "new_project_n2_observability_audit"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {output}")
    output.mkdir(parents=True)
    rows: list[dict[str, int | float | str]] = []
    for controller in ("random_no_commit", "scripted_legal_heuristic"):
        for seed in EVAL_SEEDS:
            env = make_env(mission_cfg(7201, out_dir=output / "template", updates=1), seed, training=False)
            obs, _share, _graph = env.reset()
            available_counts = np.zeros(env.num_agents, dtype=np.int64)
            direct_counts = np.zeros(env.num_agents, dtype=np.int64)
            cache_counts = np.zeros(env.num_agents, dtype=np.int64)
            steps = 0
            rng = np.random.default_rng(seed + 880_000)
            while True:
                available_counts += (np.linalg.norm(obs[:, 8:11], axis=1) > 1e-6)
                direct_counts += obs[:, 18] > 0.5
                cache_counts += obs[:, 31] > 0.0
                actions = random_no_commit(env.num_agents, rng) if controller == "random_no_commit" else scripted_legal_heuristic(obs)
                obs, _share, _graph, _reward, dones, _info = env.step(actions)
                steps += 1
                if bool(np.all(dones)):
                    break
            for agent_id in range(env.num_agents):
                rows.append({
                    "controller": controller,
                    "episode_seed": seed,
                    "agent_id": agent_id,
                    "role": int(env.config.blue_types[agent_id].role),
                    "episode_steps": steps,
                    "legal_target_available_steps": int(available_counts[agent_id]),
                    "legal_target_available_rate": float(available_counts[agent_id] / max(1, steps)),
                    "direct_sensing_steps": int(direct_counts[agent_id]),
                    "cache_confidence_positive_steps": int(cache_counts[agent_id]),
                })
    with (output / "actor_observability_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for controller in ("random_no_commit", "scripted_legal_heuristic"):
        for role in sorted({int(r["role"]) for r in rows}):
            group = [r for r in rows if r["controller"] == controller and r["role"] == role]
            summary.append({
                "controller": controller,
                "role": role,
                "actor_rows": len(group),
                "mean_legal_target_available_rate": float(np.mean([float(r["legal_target_available_rate"]) for r in group])),
                "mean_direct_sensing_steps": float(np.mean([int(r["direct_sensing_steps"]) for r in group])),
                "mean_cache_confidence_positive_steps": float(np.mean([int(r["cache_confidence_positive_steps"]) for r in group])),
            })
    with (output / "summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    print("N2_OBSERVABILITY_AUDIT_COMPLETE")
    for item in summary:
        print(item)


if __name__ == "__main__":
    main()
