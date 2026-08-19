"""Offline analysis of one-shot UTR diagnostic telemetry; never runs a policy or environment."""
from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
import statistics
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

PROTOCOL = "UTR-ONE-SHOT-MECHANISM-ANALYSIS-V1"
GOOD = (2103, 2002)
WEAK = (2102, 2104)
INTERMEDIATE = (2101,)
FAILURE_DESCRIPTORS = ("F0", "timing_early", "timing_late", "duration_short", "duration_long", "compound")


def read_jsonl(path: Path, compressed: bool = False) -> list[dict[str, Any]]:
    opener = gzip.open if compressed else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def median(values: list[float]) -> float | None:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(statistics.median(finite)) if finite else None


def mean(values: list[float]) -> float | None:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(finite) / len(finite)) if finite else None


def relative_rows(records: list[dict[str, Any]], onset: int, lower: int, upper: int) -> list[dict[str, Any]]:
    return [row for row in records if lower <= int(row["post_step"]) - onset < upper]


def action_change(rows: list[dict[str, Any]], role: int) -> float | None:
    if len(rows) < 2:
        return None
    vectors = [np.asarray(row["applied_action_components"], dtype=float)[role] for row in rows]
    return mean([float(np.linalg.norm(right - left)) for left, right in zip(vectors, vectors[1:])])


def action_energy(rows: list[dict[str, Any]], role: int) -> float | None:
    return mean([float(np.linalg.norm(np.asarray(row["applied_action_components"], dtype=float)[role])) for row in rows])


def motion_productivity(rows: list[dict[str, Any]], role: int) -> tuple[float | None, float | None, float | None]:
    if len(rows) < 2:
        return None, None, None
    positions = [np.asarray(row["physical_state_post"]["blue_position"], dtype=float)[role] for row in rows]
    length = float(sum(np.linalg.norm(right - left) for left, right in zip(positions, positions[1:])))
    displacement = float(np.linalg.norm(positions[-1] - positions[0]))
    productivity = displacement / length if length > 1e-9 else 0.0
    return length, displacement, productivity


def first_direct_time(rows: list[dict[str, Any]], onset: int) -> float | None:
    for row in records_after_onset(rows, onset):
        if int(row["path_direct_post"]) == 1:
            return float(int(row["post_step"]) - onset)
    return None


def records_after_onset(rows: list[dict[str, Any]], onset: int) -> list[dict[str, Any]]:
    return [row for row in rows if int(row["post_step"]) >= onset]


def count_switches(rows: list[dict[str, Any]], onset: int) -> int:
    paths = [str(row["task_state_post"]["existing_info"].get("attacker_cache_paths_t", ""))
             for row in records_after_onset(rows, onset)]
    return sum(left != right for left, right in zip(paths, paths[1:]))


def episode_features(summary: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    onset = summary.get("actual_failure_onset")
    if onset is None:
        onset = int(summary["scheduled_failure_onset"])
    onset = int(onset)
    immediate = relative_rows(records, onset, 0, 20)
    medium = relative_rows(records, onset, 20, 60)
    terminal = records[-80:]
    _, _, attacker_productivity = motion_productivity(medium, 2)
    _, _, scout_productivity = motion_productivity(medium, 0)
    _, _, relay_productivity = motion_productivity(medium, 1)
    task_support = mean([float(row["task_support_post"]) for row in medium])
    legal_information = mean([float(row["legal_information_post"]) for row in medium])
    tracking = mean([float(row["task_state_post"]["existing_info"].get("tracking_rate", 0.0)) for row in medium])
    attack_window = mean([float(row["task_state_post"]["existing_info"].get("attack_window_rate", 0.0)) for row in medium])
    terminal_action = action_energy(terminal, 2)
    return {
        "checkpoint_seed": int(summary["checkpoint_seed"]), "descriptor": summary["descriptor"],
        "episode_id": int(summary["development_episode_id"]), "timeout": int(summary["timeout"]),
        "collision": int(summary["collision"]), "success": int(summary["success_at_horizon"]),
        "terminal_step": int(summary["terminal_step"]),
        "scout_action_change_immediate": action_change(immediate, 0),
        "relay_action_change_immediate": action_change(immediate, 1),
        "attacker_action_change_immediate": action_change(immediate, 2),
        "attacker_action_energy_immediate": action_energy(immediate, 2),
        "attacker_productivity_medium": attacker_productivity,
        "scout_productivity_medium": scout_productivity,
        "relay_productivity_medium": relay_productivity,
        "task_support_rate_medium": task_support,
        "legal_information_rate_medium": legal_information,
        "tracking_rate_medium": tracking,
        "attack_window_rate_medium": attack_window,
        "first_direct_path_time": first_direct_time(records, onset),
        "path_switches_after_onset": count_switches(records, onset),
        "attacker_terminal_action_energy": terminal_action,
    }


def summary_by_seed_condition(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in features:
        groups[(row["checkpoint_seed"], row["descriptor"])].append(row)
    output = []
    numeric = [key for key in features[0] if key not in {"checkpoint_seed", "descriptor", "episode_id"}]
    for (seed, descriptor), rows in sorted(groups.items()):
        result: dict[str, Any] = {"checkpoint_seed": seed, "descriptor": descriptor, "episodes": len(rows)}
        for field in numeric:
            result[f"median_{field}"] = median([row[field] for row in rows])
        output.append(result)
    return output


def cell_lookup(rows: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, Any]]:
    return {(int(row["checkpoint_seed"]), str(row["descriptor"])): row for row in rows}


def group_median(cells: dict[tuple[int, str], dict[str, Any]], seeds: tuple[int, ...], descriptor: str, field: str) -> float | None:
    return median([cells[(seed, descriptor)].get(field) for seed in seeds])


def pre_registered_candidates(cells: dict[tuple[int, str], dict[str, Any]]) -> dict[str, Any]:
    """Conservative, frozen screens; no post-hoc threshold selection is allowed."""
    evidence: dict[str, Any] = {}
    for name, feature, direction in (
        ("action_adaptation_deficit", "median_attacker_action_change_immediate", "lower"),
        ("post_failure_stagnation", "median_attacker_productivity_medium", "lower"),
        ("route_oscillation", "median_path_switches_after_onset", "higher"),
    ):
        weak_cells: dict[str, dict[str, bool]] = {}
        for weak_seed in WEAK:
            per_condition: dict[str, bool] = {}
            for descriptor in FAILURE_DESCRIPTORS:
                reference = group_median(cells, GOOD, descriptor, feature)
                value = cells[(weak_seed, descriptor)].get(feature)
                timeout = cells[(weak_seed, descriptor)].get("median_timeout")
                good_timeout = group_median(cells, GOOD, descriptor, "median_timeout")
                if reference is None or value is None or timeout is None or good_timeout is None:
                    per_condition[descriptor] = False
                    continue
                if direction == "lower":
                    directional = float(value) <= 0.75 * float(reference)
                else:
                    directional = float(value) >= 1.25 * max(float(reference), 1e-9)
                per_condition[descriptor] = directional and float(timeout) >= float(good_timeout) + 0.20
            weak_cells[str(weak_seed)] = per_condition
        common = [
            descriptor for descriptor in FAILURE_DESCRIPTORS
            if all(weak_cells[str(seed)][descriptor] for seed in WEAK)
        ]
        # A candidate needs F0 plus two distinct non-F0 families in both weak seeds.
        evidence[name] = {
            "feature": feature, "direction": direction, "per_weak_seed": weak_cells,
            "common_supporting_conditions": common,
            "passes_pre_registered_pattern": "F0" in common and len(common) >= 3,
        }
    return evidence


def markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    header = "| " + " | ".join(fields) + " |"
    divider = "|" + "|".join("---" for _ in fields) + "|"
    body = []
    for row in rows:
        cells = []
        for field in fields:
            value = row.get(field)
            cells.append("—" if value is None else (f"{value:.4f}" if isinstance(value, float) else str(value)))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, divider, *body])


def write_reports(docs_root: Path, selection: dict[str, Any], cells: list[dict[str, Any]], candidates: dict[str, Any]) -> str:
    decision = "MECHANISM_IDENTIFIED" if any(value["passes_pre_registered_pattern"] for value in candidates.values()) else "NO_REPRODUCIBLE_MECHANISM_FOUND"
    selected = [
        row for row in cells if row["descriptor"] in FAILURE_DESCRIPTORS
    ]
    table = markdown_table(selected, [
        "checkpoint_seed", "descriptor", "median_timeout", "median_attacker_action_change_immediate",
        "median_attacker_productivity_medium", "median_task_support_rate_medium",
        "median_path_switches_after_onset",
    ])
    candidate_text = "\n".join(
        f"- **{name}:** pass=`{entry['passes_pre_registered_pattern']}`, "
        f"common supporting conditions={entry['common_supporting_conditions']}"
        for name, entry in candidates.items()
    )
    report = f"""# UTR Good-vs-Weak Mechanism Discovery v2\n\n**Protocol:** `{PROTOCOL}`  \n**Status:** exploratory analysis using the one-shot diagnostic telemetry only\n\n## Frozen classification\n\nPrimary ranking was locked before telemetry from Phase-D 2M UTR `J_OOD_worst`:\n\n- GOOD: {GOOD}\n- WEAK: {WEAK}\n- INTERMEDIATE: {INTERMEDIATE}\n\nAll checkpoints used the same frozen scenario IDs; episode results therefore support paired scenario description but not pseudo-replication at the training-seed level.\n\n## Pre-registered quantities\n\nThe analysis uses only immediate post-failure action change, medium-window role motion productivity, existing task-support/legal-information/tracking/attack-window state, first direct-path time, path switches, and terminal action energy. Failure windows are [0,20) and [20,60) relative to actual onset; terminal summaries use the final available 80 transitions.\n\n## Seed-condition descriptive table\n\n{table}\n\n## Candidate-pattern and counterexample screen\n\n{candidate_text}\n\nThe screens require both weak seeds to show the same direction in F0 plus at least two other failure descriptors, with elevated timeout relative to the GOOD reference. A failed screen is a counterexample to that candidate pattern, not evidence that a different mechanism should be invented.\n\n## Final chain and limitations\n\nThe final outcome is `{decision}`. The report does not claim causal proof. Any positive screen would be described only as a reproducible behavioral failure mechanism consistent with the observed degradation, and must still undergo a separately authorized method-design and prior-art review.\n"""
    report_path = docs_root / "UTR_GOOD_VS_WEAK_MECHANISM_DISCOVERY_V2.md"
    if report_path.exists():
        raise FileExistsError(f"refusing to overwrite report: {report_path}")
    report_path.write_text(report, encoding="utf-8")
    decision_text = f"""# UTR Mechanism Discovery v2 Decision\n\n**Final status:** `{decision}`\n\nThe result follows the pre-registered good/weak ranking, seven existing descriptors, fixed first-50 historical scenario IDs, passive logger invariance gate, and cross-weak-seed pattern rule. No algorithm was designed, modified, or trained.\n\nIf the status is `MECHANISM_IDENTIFIED`, it means only that a reproducible behavioral target has been found; it does not authorize method design or training. If it is `NO_REPRODUCIBLE_MECHANISM_FOUND`, the algorithm-development route closes under the one-shot protocol.\n"""
    decision_path = docs_root / "UTR_MECHANISM_DISCOVERY_V2_DECISION.md"
    if decision_path.exists():
        raise FileExistsError(f"refusing to overwrite report: {decision_path}")
    decision_path.write_text(decision_text, encoding="utf-8")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=Path("artifacts/diagnostics/utr_mechanism_v2"))
    parser.add_argument("--docs-root", type=Path, default=Path("docs"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: --execute is required for offline analysis")
    root = args.input_root.resolve(); docs_root = args.docs_root.resolve()
    selection = json.loads((root / "selection_manifest.json").read_text(encoding="utf-8"))
    if selection.get("good_weak_ranking_frozen_before_telemetry", {}).get("good") != list(GOOD):
        raise RuntimeError("good/weak classification provenance mismatch")
    summaries = read_jsonl(root / "raw" / "episode_summaries.jsonl")
    records = read_jsonl(root / "raw" / "telemetry.jsonl.gz", compressed=True)
    expected = int(selection["expected_diagnostic_episodes"])
    if len(summaries) != expected or not records:
        raise RuntimeError("incomplete telemetry data")
    grouped: dict[tuple[int, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[(int(row["checkpoint_seed"]), str(row["descriptor"]), int(row["development_episode_id"]))].append(row)
    features = []
    for summary in summaries:
        key = (int(summary["checkpoint_seed"]), str(summary["descriptor"]), int(summary["development_episode_id"]))
        if key not in grouped:
            raise RuntimeError(f"missing step records for {key}")
        features.append(episode_features(summary, grouped[key]))
    cells = summary_by_seed_condition(features)
    if len(cells) != 35:
        raise RuntimeError(f"expected 35 seed-condition cells, found {len(cells)}")
    candidates = pre_registered_candidates(cell_lookup(cells))
    (root / "derived").mkdir(exist_ok=False)
    (root / "derived" / "episode_features.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in features), encoding="utf-8"
    )
    (root / "derived" / "seed_condition_summary.json").write_text(
        json.dumps(cells, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (root / "derived" / "pre_registered_candidate_screen.json").write_text(
        json.dumps(candidates, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    decision = write_reports(docs_root, selection, cells, candidates)
    print(json.dumps({"status": "completed", "decision": decision, "episodes": len(summaries), "steps": len(records)}, indent=2))


if __name__ == "__main__":
    main()
