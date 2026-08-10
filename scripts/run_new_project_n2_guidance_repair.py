"""One authorized N2 guidance-level action-interface repair.

This is development-only: vanilla MAPPO, unchanged reward/physics/protocol,
with a fixed own-state speed-hold controller behind a 9-command turn/climb
guidance interface. No new network or formal evidence is produced.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo
from scripts.run_new_project_n2_development_pilot import (
    EVAL_SEEDS,
    TRAIN_SEEDS,
    UPDATES,
    agent_actions,
    evaluate_episode,
    load_agent,
    mission_cfg,
    random_no_commit,
    summarize,
)

PROTOCOL_VERSION = "NEW_PROJECT_N2_GUIDANCE_REPAIR_V1"


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def guidance_cfg(seed: int, out_dir: Path):
    cfg = mission_cfg(seed, out_dir=out_dir, updates=UPDATES)
    cfg.guidance_level_action_interface = True
    cfg.run_id = f"vanilla_mappo_n2_guidance_seed{seed}"
    cfg.method_label = "vanilla_mappo_n2_guidance_repair"
    cfg.protocol_version = PROTOCOL_VERSION
    return cfg


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    output = ROOT / "results" / "new_project_n2_guidance_repair"
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite guidance repair output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    template = guidance_cfg(TRAIN_SEEDS[0], output / "template")
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "performance_use_prohibited": True,
        "source_commit": source_commit(),
        "training_seeds": list(TRAIN_SEEDS),
        "evaluation_seeds": list(EVAL_SEEDS),
        "updates": UPDATES,
        "changed_factor_only": "guidance_level_action_interface=True",
        "reward_changed": False,
        "mission_physics_changed": False,
        "controller": "fixed own-state speed-hold; no target/global truth",
        "config": asdict(template),
    }
    (output / "N2_GUIDANCE_REPAIR_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    trained = []
    for seed in TRAIN_SEEDS:
        run_dir = output / f"vanilla_mappo_n2_guidance_seed{seed}"
        cfg = guidance_cfg(seed, run_dir)
        checkpoint = run_dir / "actor_critic_latest.pt"
        if not checkpoint.exists():
            print(f"guidance repair training start: seed={seed}, updates={UPDATES}", flush=True)
            train_ri_gmappo(cfg)
        trained.append((f"vanilla_mappo_n2_guidance_seed{seed}", cfg, load_agent(cfg, checkpoint)))

    eval_cfg = guidance_cfg(TRAIN_SEEDS[0], output / "template")
    rows = []
    for seed in EVAL_SEEDS:
        rng = np.random.default_rng(seed + 990_000)
        rows.append(evaluate_episode(eval_cfg, seed, "random_no_commit_guidance", lambda o, s, g, rng=rng: random_no_commit(o.shape[0], rng)))
        for name, _cfg, agent in trained:
            rows.append(evaluate_episode(eval_cfg, seed, name, lambda o, s, g, agent=agent: agent_actions(agent, o, s, g)))
    summary = summarize(rows)
    write_csv(output / "episode_outcomes.csv", rows)
    write_csv(output / "summary.csv", summary)
    learned = [item for item in summary if str(item["controller"]).startswith("vanilla_mappo_n2_guidance")]
    pooled = {
        "episodes": sum(int(item["episodes"]) for item in learned),
        "rmtn180": float(np.mean([float(item["rmtn180"]) for item in learned])),
        "neutralization_incidence180": float(np.mean([float(item["neutralization_incidence180"]) for item in learned])),
    }
    verdict = "N2_LEARNABILITY_PASS" if pooled["neutralization_incidence180"] > 0.0 and pooled["rmtn180"] < 180.0 and pooled["neutralization_incidence180"] <= 0.879 else "N2_GUIDANCE_REPAIR_NO_GO"
    (output / "N2_GUIDANCE_REPAIR_VERDICT.json").write_text(json.dumps({"verdict": verdict, "pooled_vanilla_mappo": pooled, "summary": summary}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "pooled_vanilla_mappo": pooled}, indent=2), flush=True)


if __name__ == "__main__":
    main()
