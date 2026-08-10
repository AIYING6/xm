"""Read-only localization of the N2 zero-neutralization result.

No training occurs.  Existing vanilla-MAPPO checkpoints are evaluated under:
baseline actions, evaluator auto-commit, and oracle-motion with policy commit.
All diagnostics are non-evidentiary and use true geometry only for the
diagnostic intervention and measurement.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_new_project_n2_development_pilot import agent_actions, load_agent, mission_cfg  # noqa: E402
from scripts.calibrate_new_project_n1_mission_timing import scripted_oracle_actions  # noqa: E402
from scripts.run_new_project_n2_reward_repair_pilot import repair_cfg  # noqa: E402
from envs.uav_intercept_3d_env import FLIGHT_ACTION_DIM  # noqa: E402


EVAL_SEEDS = tuple(range(730_000, 730_048))
HORIZON = 360


def commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def geometry_flags(env) -> np.ndarray:
    return np.asarray(
        [env._in_true_standoff_envelope(i, typ) for i, typ in enumerate(env.config.blue_types)],
        dtype=bool,
    )


def outcome(info: dict[str, float]) -> str:
    if float(info.get("collision", 0.0)) > 0.5:
        return "COLLISION"
    if float(info.get("constraint_violation", 0.0)) > 0.5:
        return "CONSTRAINT_FAILURE"
    if float(info.get("target_neutralized", 0.0)) > 0.5:
        return "NEUTRALIZED"
    if float(info.get("target_escape", 0.0)) > 0.5:
        return "TARGET_ESCAPE"
    return "TIMEOUT"


def run_episode(env_cfg, agent, mode: str, seed: int, checkpoint_label: str) -> dict[str, int | float | str]:
    env = __import__("algorithms.ri_gmappo.simple_ri_gmappo", fromlist=["make_env"]).make_env(env_cfg, seed, training=False)
    obs, share_obs, graph = env.reset()
    entry = False
    dwell = 0
    max_dwell = 0
    total_geometry_steps = 0
    commit_steps = 0
    aligned_commit_steps = 0
    auto_commit_steps = 0
    oracle_motion_geometry_steps = 0
    while True:
        geom = geometry_flags(env)
        legal_geom = bool(np.any(geom))
        entry = entry or legal_geom
        dwell = dwell + 1 if legal_geom else 0
        max_dwell = max(max_dwell, dwell)
        total_geometry_steps += int(legal_geom)
        proposed = agent_actions(agent, obs, share_obs, graph)
        proposed_flight = proposed % FLIGHT_ACTION_DIM
        proposed_commit = proposed >= FLIGHT_ACTION_DIM
        commit_steps += int(np.sum(proposed_commit))
        aligned_commit_steps += int(np.sum(proposed_commit & geom))

        if mode == "baseline":
            actions = proposed
        elif mode == "auto_commit":
            actions = proposed_flight + FLIGHT_ACTION_DIM * geom.astype(np.int64)
            auto_commit_steps += int(np.sum(geom))
        elif mode == "oracle_motion_policy_commit":
            oracle = scripted_oracle_actions(env)
            actions = (oracle % FLIGHT_ACTION_DIM) + FLIGHT_ACTION_DIM * proposed_commit.astype(np.int64)
            oracle_motion_geometry_steps += int(legal_geom)
        else:
            raise ValueError(mode)

        obs, share_obs, graph, _reward, dones, info = env.step(actions)
        if bool(np.all(dones)):
            return {
                "checkpoint": checkpoint_label,
                "mode": mode,
                "episode_seed": seed,
                "outcome": outcome(info),
                "terminal_step": int(info["step"]),
                "geometry_entry": int(entry),
                "geometry_dwell_max": max_dwell,
                "geometry_steps": total_geometry_steps,
                "commit_steps": commit_steps,
                "commit_alignment_steps": aligned_commit_steps,
                "commit_alignment_rate": float(aligned_commit_steps / max(1, commit_steps)),
                "auto_commit_steps": auto_commit_steps,
                "oracle_motion_geometry_steps": oracle_motion_geometry_steps,
            }


def main() -> None:
    output = ROOT / "results" / "new_project_n2_failure_localization"
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite localization output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    checkpoints = [
        ("n2_seed7201", ROOT / "results/new_project_n2_development_pilot/vanilla_mappo_n2_seed7201/actor_critic_latest.pt", mission_cfg(7201, out_dir=output / "template")),
        ("n2_seed7202", ROOT / "results/new_project_n2_development_pilot/vanilla_mappo_n2_seed7202/actor_critic_latest.pt", mission_cfg(7202, out_dir=output / "template")),
        ("repair_seed7201", ROOT / "results/new_project_n2_reward_repair_pilot/vanilla_mappo_n2_repair_seed7201/actor_critic_latest.pt", repair_cfg(7201, output / "template")),
        ("repair_seed7202", ROOT / "results/new_project_n2_reward_repair_pilot/vanilla_mappo_n2_repair_seed7202/actor_critic_latest.pt", repair_cfg(7202, output / "template")),
    ]
    rows = []
    for label, checkpoint, cfg in checkpoints:
        if not checkpoint.exists():
            raise FileNotFoundError(checkpoint)
        agent = load_agent(cfg, checkpoint)
        for mode in ("baseline", "auto_commit", "oracle_motion_policy_commit"):
            for seed in EVAL_SEEDS:
                rows.append(run_episode(cfg, agent, mode, seed, label))
    with (output / "localization_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for label in sorted({str(row["checkpoint"]) for row in rows}):
        for mode in ("baseline", "auto_commit", "oracle_motion_policy_commit"):
            group = [r for r in rows if r["checkpoint"] == label and r["mode"] == mode]
            summary.append({
                "checkpoint": label,
                "mode": mode,
                "episodes": len(group),
                "geometry_entry_rate": float(np.mean([int(r["geometry_entry"]) for r in group])),
                "mean_geometry_dwell_max": float(np.mean([int(r["geometry_dwell_max"]) for r in group])),
                "p90_geometry_dwell_max": float(np.quantile([int(r["geometry_dwell_max"]) for r in group], 0.90)),
                "mean_commit_steps": float(np.mean([int(r["commit_steps"]) for r in group])),
                "mean_commit_alignment_rate": float(np.mean([float(r["commit_alignment_rate"]) for r in group])),
                "neutralization_rate": float(np.mean([r["outcome"] == "NEUTRALIZED" for r in group])),
                "escape_rate": float(np.mean([r["outcome"] == "TARGET_ESCAPE" for r in group])),
            })
    with (output / "localization_summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    with (output / "LOCALIZATION_MANIFEST.json").open("x", encoding="utf-8") as handle:
        json.dump({
            "status": "N2_FAILURE_LOCALIZATION_COMPLETE",
            "performance_use_prohibited": True,
            "source_commit": commit(),
            "episodes_per_checkpoint_mode": len(EVAL_SEEDS),
            "modes": ["baseline", "auto_commit", "oracle_motion_policy_commit"],
            "oracle_motion_is_diagnostic_only": True,
            "no_training": True,
            "summary": summary,
        }, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("N2_FAILURE_LOCALIZATION_COMPLETE")
    for item in summary:
        print(item)


if __name__ == "__main__":
    main()
