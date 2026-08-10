"""Run the single authorized N2 potential-shaping repair pilot."""

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

from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
from scripts.run_new_project_n2_development_pilot import (  # noqa: E402
    EVAL_SEEDS,
    PROTOCOL_VERSION as BASE_PROTOCOL,
    RMTN_HORIZON,
    TRAIN_SEEDS,
    agent_actions,
    evaluate_episode,
    load_agent,
    mission_cfg,
    random_no_commit,
    scripted_legal_heuristic,
    summarize,
)


PROTOCOL_VERSION = "NEW_PROJECT_N2_REWARD_REPAIR_PILOT_V1"


def repair_cfg(seed: int, output: Path):
    cfg = mission_cfg(seed, out_dir=output)
    cfg.mission_progress_shaping_enabled = True
    return cfg


def commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def main() -> None:
    output = ROOT / "results" / "new_project_n2_reward_repair_pilot"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite repair pilot: {output}")
    output.mkdir(parents=True)
    template = repair_cfg(TRAIN_SEEDS[0], output / "template")
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "base_protocol": BASE_PROTOCOL,
        "performance_use_prohibited": True,
        "source_commit": commit(),
        "training_seeds": list(TRAIN_SEEDS),
        "evaluation_seeds": list(EVAL_SEEDS),
        "updates": 60,
        "changed_factor_only": "mission_progress_shaping_enabled=True",
        "primary_metric": "RMTN180",
        "config": asdict(template),
    }
    with (output / "N2_REPAIR_MANIFEST.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")

    trained = []
    for seed in TRAIN_SEEDS:
        run_dir = output / f"vanilla_mappo_n2_repair_seed{seed}"
        cfg = repair_cfg(seed, run_dir)
        print(f"N2 repair training start: seed={seed}, updates={cfg.updates}", flush=True)
        train_ri_gmappo(cfg)
        trained.append((f"vanilla_mappo_n2_repair_seed{seed}", cfg, load_agent(cfg, run_dir / "actor_critic_latest.pt")))

    eval_cfg = repair_cfg(TRAIN_SEEDS[0], output / "template")
    rows = []
    for seed in EVAL_SEEDS:
        rng = np.random.default_rng(seed + 880_000)
        rows.append(evaluate_episode(eval_cfg, seed, "random_no_commit", lambda o, s, g, rng=rng: random_no_commit(o.shape[0], rng)))
        rows.append(evaluate_episode(eval_cfg, seed, "scripted_legal_heuristic", lambda o, s, g: scripted_legal_heuristic(o)))
        for name, _cfg, agent in trained:
            rows.append(evaluate_episode(eval_cfg, seed, name, lambda o, s, g, agent=agent: agent_actions(agent, o, s, g)))
    with (output / "episode_outcomes.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize(rows)
    with (output / "summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    learned = [r for r in summary if str(r["controller"]).startswith("vanilla_mappo_n2_repair")]
    pooled = {
        "episodes": sum(int(r["episodes"]) for r in learned),
        "rmtn180": float(np.mean([float(r["rmtn180"]) for r in learned])),
        "neutralization_incidence180": float(np.mean([float(r["neutralization_incidence180"]) for r in learned])),
        "terminal_failure_incidence180": float(np.mean([float(r["terminal_failure_incidence180"]) for r in learned])),
    }
    verdict = (
        "N2_LEARNABILITY_PASS__READY_FOR_N3_METHOD_SELECTION"
        if pooled["neutralization_incidence180"] > 0.0 and pooled["rmtn180"] < RMTN_HORIZON and pooled["neutralization_incidence180"] <= 0.879
        else "N2_REPAIR_NO_GO__TASK_LEARNABILITY_NOT_ESTABLISHED"
    )
    with (output / "N2_REPAIR_VERDICT.json").open("x", encoding="utf-8") as handle:
        json.dump({"verdict": verdict, "pooled_repair": pooled, "summary": summary}, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"verdict": verdict, "pooled_repair": pooled}, indent=2), flush=True)


if __name__ == "__main__":
    main()
