#!/usr/bin/env python3
"""Zero-training T2 analysis of the frozen T1 native telemetry.

This program reads existing raw telemetry only.  It never instantiates an
environment, loads a policy, or writes to a T1 artifact.  Its outputs are
derived offline evidence under ``results/development/t2_*``.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any


SEEDS = (2201, 2202, 2203, 2204, 2205)
GOOD = (2202, 2204)
WEAK = (2203, 2205)
INTERMEDIATE = (2201,)
FAILURE_CONDITIONS = ("f0_seen_44_80", "timing_28_80", "duration_44_120")
WINDOWS = {
    "pre": (-20, 0),
    "early": (0, 20),
    "mid": (20, 60),
    "late": (60, 120),
}
TERMINAL_WINDOWS = (20, 40, 80)
ROLES = ("scout", "relay", "attacker")


def safe_mean(values: list[float]) -> float | None:
    return mean(values) if values else None


def norm(vector: list[float]) -> float:
    return math.sqrt(sum(float(value) ** 2 for value in vector))


def dist(a: list[float], b: list[float]) -> float:
    return norm([float(x) - float(y) for x, y in zip(a, b)])


def fmt(value: float | None, digits: int = 3) -> str:
    return "NA" if value is None else f"{value:.{digits}f}"


@dataclass
class WindowAccumulator:
    count: int = 0
    rewards: list[float] = field(default_factory=list)
    support: list[float] = field(default_factory=list)
    legal_info: list[float] = field(default_factory=list)
    cache_age: list[float] = field(default_factory=list)
    direct: list[float] = field(default_factory=list)
    relay_path: list[float] = field(default_factory=list)
    chain: list[float] = field(default_factory=list)
    action_mag: dict[str, list[float]] = field(
        default_factory=lambda: {role: [] for role in ROLES}
    )
    action_delta: dict[str, list[float]] = field(
        default_factory=lambda: {role: [] for role in ROLES}
    )
    speed: dict[str, list[float]] = field(
        default_factory=lambda: {role: [] for role in ROLES}
    )
    target_distance: dict[str, list[float]] = field(
        default_factory=lambda: {role: [] for role in ROLES}
    )
    path_length: dict[str, float] = field(
        default_factory=lambda: {role: 0.0 for role in ROLES}
    )
    first_position: dict[str, list[float] | None] = field(
        default_factory=lambda: {role: None for role in ROLES}
    )
    last_position: dict[str, list[float] | None] = field(
        default_factory=lambda: {role: None for role in ROLES}
    )
    first_target_distance: dict[str, float | None] = field(
        default_factory=lambda: {role: None for role in ROLES}
    )
    last_target_distance: dict[str, float | None] = field(
        default_factory=lambda: {role: None for role in ROLES}
    )
    previous_path: str | None = None
    path_switches: int = 0

    def update(self, step: dict[str, Any]) -> None:
        self.count += 1
        self.rewards.append(step["reward"])
        self.support.append(step["support"])
        self.legal_info.append(step["legal_info"])
        self.cache_age.append(step["cache_age"])
        self.direct.append(1.0 if step["path"] == "0-2" else 0.0)
        self.relay_path.append(1.0 if step["path"] == "0-1-2" else 0.0)
        self.chain.append(step["chain"])
        if self.previous_path is not None and step["path"] != self.previous_path:
            self.path_switches += 1
        self.previous_path = step["path"]
        for index, role in enumerate(ROLES):
            position = step["positions"][index]
            target_distance = step["target_distances"][index]
            self.action_mag[role].append(step["action_magnitudes"][index])
            if step["action_deltas"][index] is not None:
                self.action_delta[role].append(step["action_deltas"][index])
            self.speed[role].append(step["speeds"][index])
            self.target_distance[role].append(target_distance)
            if self.first_position[role] is None:
                self.first_position[role] = position
                self.first_target_distance[role] = target_distance
            self.last_position[role] = position
            self.last_target_distance[role] = target_distance
            self.path_length[role] += step["position_deltas"][index]

    def flatten(self, prefix: str) -> dict[str, float | int | None]:
        values: dict[str, float | int | None] = {
            f"{prefix}_n": self.count,
            f"{prefix}_reward_mean": safe_mean(self.rewards),
            f"{prefix}_support_mean": safe_mean(self.support),
            f"{prefix}_legal_information_mean": safe_mean(self.legal_info),
            f"{prefix}_cache_age_mean": safe_mean(self.cache_age),
            f"{prefix}_direct_path_fraction": safe_mean(self.direct),
            f"{prefix}_relay_path_fraction": safe_mean(self.relay_path),
            f"{prefix}_chain_support_mean": safe_mean(self.chain),
            f"{prefix}_path_switch_count": self.path_switches,
        }
        for role in ROLES:
            first_position = self.first_position[role]
            last_position = self.last_position[role]
            values.update(
                {
                    f"{prefix}_{role}_speed_mean": safe_mean(self.speed[role]),
                    f"{prefix}_{role}_action_magnitude_mean": safe_mean(
                        self.action_mag[role]
                    ),
                    f"{prefix}_{role}_action_change_mean": safe_mean(
                        self.action_delta[role]
                    ),
                    f"{prefix}_{role}_target_distance_mean": safe_mean(
                        self.target_distance[role]
                    ),
                    f"{prefix}_{role}_target_progress": (
                        None
                        if self.first_target_distance[role] is None
                        else self.first_target_distance[role]
                        - self.last_target_distance[role]
                    ),
                    f"{prefix}_{role}_path_length": self.path_length[role],
                    f"{prefix}_{role}_net_displacement": (
                        None
                        if first_position is None or last_position is None
                        else dist(first_position, last_position)
                    ),
                }
            )
        return values


@dataclass
class EpisodeAccumulator:
    seed: int
    episode_id: int
    scenario: str
    scheduled_onset: int
    scheduled_duration: int
    windows: dict[str, WindowAccumulator] = field(
        default_factory=lambda: {name: WindowAccumulator() for name in WINDOWS}
    )
    terminal_steps: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=80))
    actual_onset: int | None = None
    terminal_step: int = 0
    terminal_flags: dict[str, float] = field(default_factory=dict)
    last_path: str | None = None
    all_path_switches: int = 0

    def update(self, step: dict[str, Any]) -> None:
        if step["failure_active"] and self.actual_onset is None:
            self.actual_onset = step["post_step"]
        tau = step["post_step"] - self.scheduled_onset
        for name, (lower, upper) in WINDOWS.items():
            if lower <= tau < upper:
                self.windows[name].update(step)
        self.terminal_steps.append(step)
        if self.last_path is not None and step["path"] != self.last_path:
            self.all_path_switches += 1
        self.last_path = step["path"]
        self.terminal_step = step["post_step"]
        self.terminal_flags = step["flags"]

    def finalize(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "seed": self.seed,
            "episode_id": self.episode_id,
            "scenario": self.scenario,
            "scheduled_failure_onset": self.scheduled_onset,
            "scheduled_failure_duration": self.scheduled_duration,
            "actual_failure_onset": self.actual_onset,
            "failure_onset_matches_schedule": (
                None
                if self.actual_onset is None
                else self.actual_onset == self.scheduled_onset
            ),
            "terminal_step": self.terminal_step,
            "failure_exposed": int(self.actual_onset is not None),
            "survived_to_scheduled_onset": int(self.terminal_step >= self.scheduled_onset),
            "all_path_switch_count": self.all_path_switches,
            **self.terminal_flags,
        }
        for name, accumulator in self.windows.items():
            result.update(accumulator.flatten(name))
        all_terminal = list(self.terminal_steps)
        for width in TERMINAL_WINDOWS:
            accumulator = WindowAccumulator()
            for step in all_terminal[-width:]:
                accumulator.update(step)
            result.update(accumulator.flatten(f"terminal_{width}"))
        return result


def extract_step(row: dict[str, Any], previous_positions: list[list[float]] | None,
                 previous_actions: list[list[float]] | None) -> tuple[dict[str, Any], list[list[float]], list[list[float]]]:
    diagnostic = row["diagnostic"]
    info = diagnostic["info"]
    positions = [[float(v) for v in p] for p in diagnostic["blue_position"]]
    target = [float(v) for v in diagnostic["red_position"][0]]
    actions = [[float(v) for v in a] for a in row["applied_action_components"]]
    position_deltas = (
        [0.0, 0.0, 0.0]
        if previous_positions is None
        else [dist(p, q) for p, q in zip(positions, previous_positions)]
    )
    action_deltas: list[float | None] = (
        [None, None, None]
        if previous_actions is None
        else [dist(a, b) for a, b in zip(actions, previous_actions)]
    )
    step = {
        "post_step": int(row["post_step"]),
        "failure_active": bool(row["failure_active_post"]),
        "reward": float(row["reward_sum_step"]),
        "support": float(info["chain_support_t"]),
        "legal_info": float(info["attacker_legal_target_information_t"]),
        "cache_age": float(info["target_cache_age_mean"]),
        "path": str(info["attacker_cache_paths_t"]),
        "chain": float(info["chain_support_t"]),
        "positions": positions,
        "target_distances": [dist(p, target) for p in positions],
        "speeds": [float(v) for v in diagnostic["blue_speed"]],
        "action_magnitudes": [norm(a) for a in actions],
        "action_deltas": action_deltas,
        "position_deltas": position_deltas,
        "flags": {
            "collision": float(info["collision"]),
            "timeout": float(info["timeout"]),
            "constraint_violation": float(info["constraint_violation"]),
            "success": float(info["success"]),
        },
    }
    return step, positions, actions


def load_aggregate_map(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    result: dict[tuple[str, int], dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            result[(record["scenario"], int(record["episode_id"]))] = record
    return result


def analyze_seed(seed: int, raw_path: Path, aggregate_path: Path) -> list[dict[str, Any]]:
    aggregates = load_aggregate_map(aggregate_path)
    episodes: dict[tuple[str, int], EpisodeAccumulator] = {}
    previous_positions: dict[tuple[str, int], list[list[float]]] = {}
    previous_actions: dict[tuple[str, int], list[list[float]]] = {}
    with raw_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            key = (str(row["scenario"]), int(row["episode_id"]))
            if key not in episodes:
                episodes[key] = EpisodeAccumulator(
                    seed=seed,
                    episode_id=key[1],
                    scenario=key[0],
                    scheduled_onset=int(row["scheduled_failure_onset"]),
                    scheduled_duration=int(row["scheduled_failure_duration"]),
                )
            step, positions, actions = extract_step(
                row, previous_positions.get(key), previous_actions.get(key)
            )
            episodes[key].update(step)
            previous_positions[key] = positions
            previous_actions[key] = actions
    records: list[dict[str, Any]] = []
    for key, episode in episodes.items():
        record = episode.finalize()
        aggregate = aggregates[key]
        record.update({
            "J": float(aggregate["J"]),
            "aggregate_failure_exposed": int(aggregate["failure_exposed"]),
            "aggregate_path_switch_count": int(aggregate["path_switch_count"]),
            "aggregate_step_count": int(aggregate["step_count"]),
        })
        records.append(record)
    return records


def numeric_mean(records: list[dict[str, Any]], key: str) -> float | None:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return safe_mean(values)


def condition_seed_records(records: list[dict[str, Any]], seed: int, scenario: str) -> list[dict[str, Any]]:
    return [record for record in records if record["seed"] == seed and record["scenario"] == scenario]


def seed_summary(records: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    nominal = condition_seed_records(records, seed, "nominal")
    f0 = condition_seed_records(records, seed, "f0_seen_44_80")
    ood = [r for r in records if r["seed"] == seed and r["scenario"] not in {"nominal", "f0_seen_44_80"}]
    condition_j = {}
    for scenario in sorted({r["scenario"] for r in records if r["seed"] == seed and r["scenario"] != "nominal"}):
        condition_j[scenario] = numeric_mean(condition_seed_records(records, seed, scenario), "J")
    return {
        "seed": seed,
        "J_nominal": numeric_mean(nominal, "J"),
        "J_F0": numeric_mean(f0, "J"),
        "J_OOD_mean": safe_mean(
            [value for condition, value in condition_j.items() if condition != "f0_seen_44_80"]
        ),
        "J_OOD_worst": min(
            value for condition, value in condition_j.items() if condition != "f0_seen_44_80"
        ),
        "collision": numeric_mean([r for r in records if r["seed"] == seed], "collision"),
        "timeout": numeric_mean([r for r in records if r["seed"] == seed], "timeout"),
        "constraint_violation": numeric_mean([r for r in records if r["seed"] == seed], "constraint_violation"),
        "survival_to_onset_fraction": numeric_mean(
            [r for r in records if r["seed"] == seed and r["scenario"] != "nominal"],
            "survived_to_scheduled_onset",
        ),
        "failure_trigger_success_among_risk_set": None,  # filled below
        "pre_trigger_collision_rate": None,
        "condition_J": condition_j,
    }


def fill_trigger_metrics(summary: dict[str, Any], records: list[dict[str, Any]]) -> None:
    failure_records = [r for r in records if r["scenario"] != "nominal"]
    risk_set = [r for r in failure_records if r["survived_to_scheduled_onset"]]
    summary["failure_trigger_success_among_risk_set"] = numeric_mean(risk_set, "failure_exposed")
    summary["pre_trigger_collision_rate"] = safe_mean(
        [
            1.0
            if r["terminal_step"] < r["scheduled_failure_onset"] and r["collision"]
            else 0.0
            for r in failure_records
        ]
    )


def group_window_statistics(records: list[dict[str, Any]], scenario: str, window: str, metric: str) -> dict[str, Any]:
    key = f"{window}_{metric}"
    by_seed = {
        seed: numeric_mean(condition_seed_records(records, seed, scenario), key) for seed in GOOD + WEAK
    }
    good_values = [by_seed[s] for s in GOOD if by_seed[s] is not None]
    weak_values = [by_seed[s] for s in WEAK if by_seed[s] is not None]
    difference = None if not good_values or not weak_values else mean(good_values) - mean(weak_values)
    pair_diffs = {
        f"good{good}_weak{weak}": None
        if by_seed[good] is None or by_seed[weak] is None
        else by_seed[good] - by_seed[weak]
        for good in GOOD for weak in WEAK
    }
    signs = [value for value in pair_diffs.values() if value is not None and value != 0]
    same_direction = bool(signs) and (all(v > 0 for v in signs) or all(v < 0 for v in signs))
    return {
        "scenario": scenario,
        "window": window,
        "metric": metric,
        "good_seed_means": {str(seed): by_seed[seed] for seed in GOOD},
        "weak_seed_means": {str(seed): by_seed[seed] for seed in WEAK},
        "good_minus_weak": difference,
        "pairwise_differences": pair_diffs,
        "all_four_good_weak_pairs_same_direction": same_direction,
    }


def episode_paired_difference(records: list[dict[str, Any]], scenario: str, window: str, metric: str) -> dict[str, Any]:
    key = f"{window}_{metric}"
    values: dict[tuple[int, int], float] = {}
    for record in records:
        if record["scenario"] == scenario and record["seed"] in GOOD + WEAK and record.get(key) is not None:
            values[(record["seed"], record["episode_id"])] = float(record[key])
    paired: list[float] = []
    for episode_id in sorted({episode for _, episode in values}):
        good = [values[(seed, episode_id)] for seed in GOOD if (seed, episode_id) in values]
        weak = [values[(seed, episode_id)] for seed in WEAK if (seed, episode_id) in values]
        if len(good) == len(GOOD) and len(weak) == len(WEAK):
            paired.append(mean(good) - mean(weak))
    return {
        "scenario": scenario,
        "window": window,
        "metric": metric,
        "paired_descriptor_count": len(paired),
        "good_minus_weak_mean": safe_mean(paired),
        "positive_fraction": safe_mean([1.0 if value > 0 else 0.0 for value in paired]),
    }


def build_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = [seed_summary(records, seed) for seed in SEEDS]
    for summary in summaries:
        fill_trigger_metrics(summary, [r for r in records if r["seed"] == summary["seed"]])
    rankings = sorted(summaries, key=lambda item: (-item["J_OOD_worst"], item["timeout"], -item["J_OOD_mean"], -item["J_F0"]))
    ranking_rows = [{**row, "rank": index + 1} for index, row in enumerate(rankings)]
    candidate_metrics = (
        "attacker_target_progress",
        "attacker_target_distance_mean",
        "attacker_net_displacement",
        "attacker_path_length",
        "attacker_action_change_mean",
        "support_mean",
        "legal_information_mean",
        "cache_age_mean",
        "direct_path_fraction",
        "relay_path_fraction",
        "path_switch_count",
    )
    window_rows = []
    paired_rows = []
    for scenario in FAILURE_CONDITIONS:
        for window in WINDOWS:
            for metric in candidate_metrics:
                window_rows.append(group_window_statistics(records, scenario, window, metric))
                paired_rows.append(episode_paired_difference(records, scenario, window, metric))
        for width in TERMINAL_WINDOWS:
            terminal_window = f"terminal_{width}"
            for metric in candidate_metrics:
                window_rows.append(group_window_statistics(records, scenario, terminal_window, metric))
                paired_rows.append(episode_paired_difference(records, scenario, terminal_window, metric))
    onset_mismatches = [
        r for r in records if r["scenario"] != "nominal" and r["failure_exposed"] and not r["failure_onset_matches_schedule"]
    ]
    return {
        "protocol": "T2-TELEMETRY-NATIVE-MECHANISM-ANALYSIS-V1",
        "source_only": True,
        "record_count": len(records),
        "seed_summaries": summaries,
        "ranked_seed_summaries": ranking_rows,
        "frozen_groups": {"GOOD": GOOD, "WEAK": WEAK, "INTERMEDIATE": INTERMEDIATE},
        "aligned_windows": WINDOWS,
        "terminal_windows": TERMINAL_WINDOWS,
        "failure_condition_families": FAILURE_CONDITIONS,
        "onset_mismatch_count": len(onset_mismatches),
        "window_comparisons": window_rows,
        "paired_descriptor_comparisons": paired_rows,
    }


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    fields = sorted({key for record in records for key in record})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def read_feature_csv(path: Path) -> list[dict[str, Any]]:
    """Read a prior derived feature table without rereading raw telemetry.

    This exists solely to correct/report analysis definitions; it does not
    create data, roll out a policy, or alter the immutable raw source.
    """
    records: list[dict[str, Any]] = []
    text_fields = {"scenario"}
    int_fields = {
        "seed", "episode_id", "scheduled_failure_onset", "scheduled_failure_duration",
        "terminal_step", "failure_exposed", "survived_to_scheduled_onset",
        "all_path_switch_count", "aggregate_failure_exposed", "aggregate_path_switch_count",
        "aggregate_step_count", "collision", "timeout", "constraint_violation", "success",
    }
    bool_fields = {"failure_onset_matches_schedule"}
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            record: dict[str, Any] = {}
            for key, value in raw.items():
                if value == "":
                    record[key] = None
                elif key in text_fields:
                    record[key] = value
                elif key in int_fields:
                    record[key] = int(float(value))
                elif key in bool_fields:
                    record[key] = value == "True"
                else:
                    record[key] = float(value)
            records.append(record)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t1-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--episode-features", type=Path)
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite derived evidence: {args.output_root}")
    if args.episode_features:
        all_records = read_feature_csv(args.episode_features)
        print(f"T2 reused {len(all_records)} previously derived episode features", flush=True)
    else:
        all_records = []
        for seed in SEEDS:
            root = args.t1_root / "evaluations" / "final_1m" / "utr_sg" / f"seed{seed}"
            all_records.extend(analyze_seed(seed, root / "raw_step_telemetry.jsonl", root / "episode_aggregates.jsonl"))
            print(f"T2 streamed T1 seed{seed}: {len(all_records)} episode aggregates", flush=True)
    args.output_root.mkdir(parents=True)
    write_csv(all_records, args.output_root / "episode_features.csv")
    analysis = build_analysis(all_records)
    (args.output_root / "t2_analysis.json").write_text(json.dumps(analysis, indent=2, allow_nan=False), encoding="utf-8")
    schema = {
        "raw_top_level": [
            "protocol", "schema_version", "episode_id", "scenario", "timestep", "post_step",
            "scheduled_failure_onset", "scheduled_failure_duration", "actor", "action_index",
            "applied_action_components", "control_effort", "reward_sum_step", "movement_distance",
            "failure_active_post", "terminal", "diagnostic",
        ],
        "actor_legal": ["actor.obs", "actor.graph_node_feat", "actor.graph_edge_feat", "actor.graph_adj", "actor.graph_relation_adj", "actor.graph_role"],
        "environment_diagnostic": ["diagnostic.blue_position", "diagnostic.red_position", "diagnostic.blue_speed", "diagnostic.blue_heading", "diagnostic.blue_gamma", "diagnostic.info.*"],
        "derived_offline": ["failure-aligned window summaries", "role path/net displacement", "target-relative progress", "action magnitude/change", "path-switch and dwell fractions", "terminal-window precursors", "GOOD-vs-WEAK paired descriptor differences"],
    }
    (args.output_root / "schema_appendix.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "output_root": str(args.output_root), "records": len(all_records)}, indent=2))


if __name__ == "__main__":
    main()
