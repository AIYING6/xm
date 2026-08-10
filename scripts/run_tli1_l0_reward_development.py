"""TLI1 reward-only paired L0 development test (non-evidentiary)."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_new_project_l0_single_interceptor as base


OUT = ROOT / "results" / "tli1_l0_reward_development"
TRAIN_SEEDS = base.TRAIN_SEEDS
EVAL_SEEDS = base.EVAL_SEEDS
UPDATES = base.UPDATES
PROTOCOL_VERSION = "TLI1_L0_REWARD_ONLY_DEVELOPMENT_V1"


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def reward_cfg(seed: int, out_dir: Path, updates: int = UPDATES):
    cfg = base.l0_cfg(seed, out_dir, updates=updates)
    return replace(
        cfg,
        mission_progress_shaping_enabled=True,
        mission_reward_alignment_v1_enabled=True,
        out_dir=str(out_dir),
        run_id=f"tli1_l0_reward_seed{seed}",
        protocol_version=PROTOCOL_VERSION,
    )


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    template = reward_cfg(TRAIN_SEEDS[0], OUT / "template", updates=1)
    manifest = {
        "status": "TLI1_REWARD_ONLY_DEVELOPMENT",
        "performance_use_prohibited": True,
        "source_commit": source_commit(),
        "training_seeds": list(TRAIN_SEEDS),
        "evaluation_seeds": list(EVAL_SEEDS),
        "updates": UPDATES,
        "only_changed_field": "mission_reward_alignment_v1_enabled=true",
        "config": asdict(template),
    }
    (OUT / "TLI1_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    trained = []
    for seed in TRAIN_SEEDS:
        run = OUT / f"tli1_l0_reward_seed{seed}"
        cfg = reward_cfg(seed, run)
        ckpt = run / "actor_critic_latest.pt"
        if not ckpt.exists():
            base.train_ri_gmappo(cfg)
        trained.append((f"tli1_l0_reward_seed{seed}", cfg, base.load_agent(cfg, ckpt)))

    rows = []
    eval_cfg = reward_cfg(TRAIN_SEEDS[0], OUT / "template", updates=1)
    for seed in EVAL_SEEDS:
        for mode in ("random", "scripted", "oracle"):
            rows.append(base.episode(eval_cfg, seed, mode))
        for name, _cfg, agent in trained:
            rows.append({**base.episode(eval_cfg, seed, name, agent), "mode": name})
    with (OUT / "episode_outcomes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = []
    for mode in sorted({r["mode"] for r in rows}):
        group = [r for r in rows if r["mode"] == mode]
        summary.append({
            "mode": mode,
            "episodes": len(group),
            "geometry_entry_rate": float(np.mean([r["geometry_entry"] for r in group])),
            "neutralization_rate": float(np.mean([r["neutralized_by_180"] for r in group])),
            "rmtn180": float(np.mean([r["rmtn180"] for r in group])),
        })
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    learned = [r for r in summary if r["mode"].startswith("tli1_l0_reward_seed")]
    seed_positive = [r for r in learned if r["geometry_entry_rate"] > 0.0 and r["neutralization_rate"] > 0.0]
    verdict = (
        "TLI1_REWARD_REALIGNMENT_ESTABLISHES_L0_LEARNING_SIGNAL"
        if len(seed_positive) == len(TRAIN_SEEDS) and all(r["rmtn180"] < 180.0 for r in learned)
        else "TLI1_REWARD_ONLY_NO_GO_OR_UNSTABLE"
    )
    payload = {"verdict": verdict, "summary": summary, "performance_use_prohibited": True}
    (OUT / "TLI1_VERDICT.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
