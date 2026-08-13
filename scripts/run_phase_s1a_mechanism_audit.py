"""Read-only audit of S1 exposure and information mechanisms.

This script never reruns the environment and never changes S1 estimands.  It
classifies existing paired traces and writes an independent audit package.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


TRIGGER_STEP = 44
ACTIVE_END_STEP = 123


def classify_exposure(group: pd.DataFrame) -> str:
    if bool(group["relay_failure_active"].max()):
        return "exposed"
    if int(group["timestep"].max()) < TRIGGER_STEP:
        return "terminated_before_failure_trigger"
    return "failure_not_active_at_or_after_trigger"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("results/development/phase_s1_paired_robustness"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/development/phase_s1a_mechanism_audit"),
    )
    args = parser.parse_args()
    episode_path = args.input_dir / "raw_episode_metrics.csv"
    timestep_paths = sorted((args.input_dir / "raw_timestep").glob("*.csv"))
    if not episode_path.exists() or not timestep_paths:
        raise FileNotFoundError("S1 raw episode/timestep artifacts are required")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    episodes = pd.read_csv(episode_path)
    timesteps = pd.concat((pd.read_csv(path) for path in timestep_paths), ignore_index=True)
    failure = timesteps[timesteps["condition"].eq("relay_failure")].copy()
    key = ["development_episode_id", "controller", "seed"]

    exposure_rows = []
    for group_key, frame in failure.groupby(key, sort=False):
        row = dict(zip(key, group_key))
        row.update(
            {
                "exposure_class": classify_exposure(frame),
                "last_timestep": int(frame["timestep"].max()),
                "n_steps": len(frame),
            }
        )
        exposure_rows.append(row)
    exposure = pd.DataFrame(exposure_rows)
    exposure.to_csv(args.output_dir / "episode_exposure_audit.csv", index=False)

    # The first active row is the frozen failure-trigger observation.  A direct
    # link later in the active window is a possible recovery path, not a trigger
    # bypass.  Keep both quantities separate.
    first_active = (
        failure[failure["relay_failure_active"].eq(1)]
        .sort_values([*key, "timestep"])
        .groupby(key, as_index=False)
        .first()
    )
    first_active = first_active.rename(
        columns={
            "scout_attacker_comm": "direct_link_at_failure_trigger",
            "attacker_direct_target_information": "direct_target_info_at_failure_trigger",
            "attacker_legal_information": "legal_info_at_failure_trigger",
            "chain_support": "chain_support_at_failure_trigger",
            "target_cache_age_mean": "cache_age_at_failure_trigger",
            "attacker_cache_path": "cache_path_at_failure_trigger",
        }
    )
    trigger_cols = key + [
        "timestep",
        "direct_link_at_failure_trigger",
        "direct_target_info_at_failure_trigger",
        "legal_info_at_failure_trigger",
        "chain_support_at_failure_trigger",
        "cache_age_at_failure_trigger",
        "cache_path_at_failure_trigger",
    ]
    first_active[trigger_cols].to_csv(args.output_dir / "failure_trigger_audit.csv", index=False)

    active = failure[failure["relay_failure_active"].eq(1)].copy()
    active["post_trigger_direct_link"] = active["scout_attacker_comm"]
    active["post_trigger_direct_target_info"] = active["attacker_direct_target_information"]
    active["post_trigger_recovery_path"] = active["attacker_cache_path"].eq("0-2").astype(int)
    mechanism = (
        active.groupby(["controller", "seed"], as_index=False)
        .agg(
            exposed_episodes=("development_episode_id", "nunique"),
            active_rows=("timestep", "size"),
            legal_info_rate=("attacker_legal_information", "mean"),
            chain_support_rate=("chain_support", "mean"),
            mean_cache_age=("target_cache_age_mean", "mean"),
            stale_or_direct_rate=("post_trigger_direct_target_info", "mean"),
            direct_link_rate=("post_trigger_direct_link", "mean"),
            direct_recovery_path_rate=("post_trigger_recovery_path", "mean"),
        )
    )
    mechanism.to_csv(args.output_dir / "exposed_mechanism_summary.csv", index=False)

    # Compact paired timeline means by phase.  Raw timestep provenance remains
    # untouched; this table is only a reproducible diagnostic view.
    phase = pd.cut(
        timesteps["timestep"],
        bins=[-1, TRIGGER_STEP - 1, ACTIVE_END_STEP, float("inf")],
        labels=["pre_trigger", "failure_active_window", "post_failure_window"],
    )
    timeline = (
        timesteps.assign(phase=phase)
        .groupby(["controller", "condition", "phase"], as_index=False, observed=False)
        .agg(
            rows=("timestep", "size"),
            legal_info_rate=("attacker_legal_information", "mean"),
            chain_support_rate=("chain_support", "mean"),
            mean_cache_age=("target_cache_age_mean", "mean"),
            direct_target_info_rate=("attacker_direct_target_information", "mean"),
            scout_attacker_comm_rate=("scout_attacker_comm", "mean"),
            reward_sum_mean=("reward_sum", "mean"),
        )
    )
    timeline.to_csv(args.output_dir / "paired_timeline_summary.csv", index=False)

    exposure_counts = exposure.groupby(["controller", "exposure_class"]).size().reset_index(name="episodes")
    exposure_counts.to_csv(args.output_dir / "exposure_class_summary.csv", index=False)
    manifest = {
        "protocol": "PHASE-S1A-EM-V1",
        "source_protocol": "PHASE-S1-RV-V1",
        "read_only": True,
        "training_started": False,
        "trigger_step": TRIGGER_STEP,
        "active_end_step": ACTIVE_END_STEP,
        "raw_episode_sha256_required": True,
        "interpretation": {
            "non_exposed": "classified, not removed or reweighted",
            "direct_bypass": "measured at first active failure row; later direct links are reported as post-trigger paths",
        },
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
