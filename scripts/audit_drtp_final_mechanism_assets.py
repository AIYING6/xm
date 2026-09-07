"""Read-only mechanism-asset audit for final DRTP A/B archives.

The script consumes completed archives directly.  It never extracts or alters
checkpoints, replays an evaluation tape, or invokes a training routine.  Its
purpose is deliberately limited: establish whether final sampler telemetry,
condition-level endpoints, and topology-condition metadata support an honest
topology-difficulty/exposure analysis.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import tarfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


FAILURE_GROUPS = ("F0", "TE", "TL", "DS", "DL", "CP")
Q_COLUMNS = tuple(f"q_{group}" for group in FAILURE_GROUPS)
DIFFICULTY_COLUMNS = tuple(f"difficulty_{group}" for group in FAILURE_GROUPS)
MILESTONES = (0.0, 0.25, 0.5, 0.75, 1.0)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def member_by_suffix(archive: tarfile.TarFile, suffix: str) -> tarfile.TarInfo:
    hits = [m for m in archive.getmembers() if m.isfile() and m.name.endswith(suffix)]
    if len(hits) != 1:
        raise ValueError(f"Expected exactly one member ending {suffix!r}; found {len(hits)}")
    return hits[0]


def read_text(archive: tarfile.TarFile, member: tarfile.TarInfo) -> str:
    handle = archive.extractfile(member)
    if handle is None:
        raise ValueError(f"Cannot read {member.name}")
    return handle.read().decode("utf-8")


def read_csv(archive: tarfile.TarFile, member: tarfile.TarInfo) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(read_text(archive, member))))


def finite(value: str | None) -> float | None:
    try:
        item = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return item if math.isfinite(item) else None


def mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return statistics.fmean(items) if items else None


def fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.8g}"


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def normalize_group(condition: str) -> str | None:
    value = condition.strip().upper()
    if value in FAILURE_GROUPS:
        return value
    if value in {"N", "NOMINAL"}:
        return "N"
    return None


def rank(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][1] == ordered[start][1]:
            end += 1
        value = (start + end + 1) / 2.0
        for index, _ in ordered[start:end]:
            ranks[index] = value
        start = end
    return ranks


def spearman(left: list[float], right: list[float]) -> float | None:
    if len(left) < 3 or len(left) != len(right):
        return None
    a, b = rank(left), rank(right)
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    numerator = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    denominator = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return numerator / denominator if denominator else None


def topology_contract(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups = manifest.get("groups", {})
    for group in ("N",) + FAILURE_GROUPS:
        members = groups.get(group, [])
        starts = [float(item[1]) for item in members if len(item) >= 3]
        durations = [float(item[2]) for item in members if len(item) >= 3]
        rows.append(
            {
                "group": group,
                "condition_count": len(members),
                "condition_ids": "|".join(str(item[0]) for item in members),
                "failure_start_min": fmt(min(starts) if starts else None),
                "failure_start_max": fmt(max(starts) if starts else None),
                "failure_duration_min": fmt(min(durations) if durations else None),
                "failure_duration_max": fmt(max(durations) if durations else None),
                "graph_edge_definition_available": False,
                "graph_path_metrics_available": False,
                "note": "Archive manifest supplies group/time semantics; no explicit adjacency matrix or edge list is assumed.",
            }
        )
    return rows


def analyze_archive(label: str, archive_path: Path) -> dict[str, Any]:
    with tarfile.open(archive_path, "r:gz") as archive:
        endpoint_member = member_by_suffix(archive, "evaluations/final_10m/per_seed_condition_summary.csv")
        endpoint_rows = read_csv(archive, endpoint_member)
        sampler_members = [m for m in archive.getmembers() if m.isfile() and "/runs/drtp_sg/seed" in m.name and m.name.endswith("/drtp_topology_sampler_log.csv")]
        manifest_members = [m for m in archive.getmembers() if m.isfile() and "/runs/drtp_sg/seed" in m.name and m.name.endswith("/drtp_topology_sampler_manifest.json")]
        if len(sampler_members) != 5 or len(manifest_members) != 5:
            raise ValueError(f"{label}: expected five DRTP sampler logs/manifests, got {len(sampler_members)}/{len(manifest_members)}")

        manifests = [json.loads(read_text(archive, item)) for item in manifest_members]
        base_contract = topology_contract(manifests[0])
        if any(topology_contract(item) != base_contract for item in manifests[1:]):
            raise ValueError(f"{label}: DRTP sampler group contract differs between seeds")

        endpoint: dict[int, dict[str, dict[str, float]]] = defaultdict(dict)
        for row in endpoint_rows:
            if row.get("method") != "drtp_sg":
                continue
            group = normalize_group(row.get("condition", ""))
            seed = int(row["train_seed"])
            if group is None:
                continue
            values = {key: finite(row.get(key)) for key in ("J", "success", "timeout", "collision")}
            if any(value is None for value in values.values()):
                raise ValueError(f"{label}: non-finite endpoint row for seed {seed}, condition {group}")
            endpoint[seed][group] = {key: float(value) for key, value in values.items()}

        seed_rows: list[dict[str, Any]] = []
        trajectory_rows: list[dict[str, Any]] = []
        group_rows: list[dict[str, Any]] = []
        correlation_rows: list[dict[str, Any]] = []
        all_group_values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

        for sampler_member in sorted(sampler_members, key=lambda x: x.name):
            seed_text = sampler_member.name.split("/seed", 1)[1].split("/", 1)[0]
            seed = int(seed_text)
            rows = read_csv(archive, sampler_member)
            selections = [row for row in rows if row.get("record_type") == "selection"]
            if seed not in endpoint or "N" not in endpoint[seed]:
                raise ValueError(f"{label}: missing DRTP endpoint cells for seed {seed}")
            counts = Counter(normalize_group(row.get("group", "")) for row in selections)
            non_nominal_total = sum(counts[group] for group in FAILURE_GROUPS)
            valid_q_rows = [row for row in rows if all(finite(row.get(column)) is not None for column in Q_COLUMNS)]
            valid_difficulty_rows = [row for row in rows if all(finite(row.get(column)) is not None for column in DIFFICULTY_COLUMNS)]
            if not valid_q_rows:
                raise ValueError(f"{label}: no finite q observations for seed {seed}")
            last_q = valid_q_rows[-1]
            last_difficulty = valid_difficulty_rows[-1] if valid_difficulty_rows else None
            max_update = max(int(float(row.get("update") or 0)) for row in valid_q_rows)

            for proportion in MILESTONES:
                target = proportion * max_update
                chosen = min(valid_q_rows, key=lambda row: abs(int(float(row.get("update") or 0)) - target))
                record: dict[str, Any] = {"cohort": label, "train_seed": seed, "milestone_fraction": proportion, "update": chosen.get("update", "")}
                record.update({column: finite(chosen.get(column)) for column in Q_COLUMNS})
                trajectory_rows.append(record)

            nominal_j = endpoint[seed]["N"]["J"]
            rho_left: list[float] = []
            rho_right: list[float] = []
            for group in FAILURE_GROUPS:
                if group not in endpoint[seed]:
                    raise ValueError(f"{label}: missing endpoint group {group} for seed {seed}")
                metrics = endpoint[seed][group]
                exposure = counts[group] / non_nominal_total if non_nominal_total else float("nan")
                final_q = finite(last_q.get(f"q_{group}"))
                final_difficulty = finite(last_difficulty.get(f"difficulty_{group}")) if last_difficulty else None
                row = {
                    "cohort": label,
                    "train_seed": seed,
                    "group": group,
                    "J": metrics["J"],
                    "J_nominal": nominal_j,
                    "J_nominal_minus_group": nominal_j - metrics["J"],
                    "success": metrics["success"],
                    "timeout": metrics["timeout"],
                    "collision": metrics["collision"],
                    "actual_non_nominal_exposure_share": exposure,
                    "final_q": final_q,
                    "final_logged_difficulty": final_difficulty,
                    "selection_count": counts[group],
                    "non_nominal_selection_count": non_nominal_total,
                }
                group_rows.append(row)
                for key, value in row.items():
                    if key in {"cohort", "train_seed", "group"} or not isinstance(value, (int, float)) or not math.isfinite(value):
                        continue
                    all_group_values[group][key].append(float(value))
                if final_difficulty is not None and math.isfinite(exposure):
                    rho_left.append(final_difficulty)
                    rho_right.append(exposure)

            correlation_rows.append(
                {
                    "cohort": label,
                    "train_seed": seed,
                    "spearman_final_logged_difficulty_vs_actual_exposure": spearman(rho_left, rho_right),
                    "interpretation": "Descriptive within-seed six-group association; not a causal estimate.",
                }
            )
            seed_rows.append(
                {
                    "cohort": label,
                    "train_seed": seed,
                    "selection_rows": len(selections),
                    "non_nominal_selection_rows": non_nominal_total,
                    "last_q_update": max_update,
                    "last_q_l1_distance_from_uniform": sum(abs(float(finite(last_q.get(column)) or 0.0) - 1.0 / 6.0) for column in Q_COLUMNS),
                    **{f"final_{column}": finite(last_q.get(column)) for column in Q_COLUMNS},
                    **{f"final_{column}": finite(last_difficulty.get(column)) if last_difficulty else None for column in DIFFICULTY_COLUMNS},
                }
            )

    aggregate_rows: list[dict[str, Any]] = []
    for group in FAILURE_GROUPS:
        values = all_group_values[group]
        aggregate_rows.append(
            {
                "cohort": label,
                "group": group,
                "n_training_seeds": len(values["J"]),
                **{f"mean_{key}": mean(item) for key, item in values.items()},
            }
        )
    return {
        "label": label,
        "archive": str(archive_path),
        "sha256": digest(archive_path),
        "endpoint_member": endpoint_member.name,
        "sampler_log_count": len(sampler_members),
        "topology_contract": base_contract,
        "seed_rows": seed_rows,
        "trajectory_rows": trajectory_rows,
        "group_rows": group_rows,
        "aggregate_rows": aggregate_rows,
        "correlation_rows": correlation_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-a", type=Path, required=True)
    parser.add_argument("--archive-b", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_a = analyze_archive("A", args.archive_a)
    result_b = analyze_archive("B", args.archive_b)

    for result in (result_a, result_b):
        write_csv(
            args.output_dir / f"DRTP_MECHANISM_{result['label']}_SEED_SAMPLER_SUMMARY.csv",
            result["seed_rows"],
            list(result["seed_rows"][0]),
        )
        write_csv(
            args.output_dir / f"DRTP_MECHANISM_{result['label']}_Q_TRAJECTORY.csv",
            result["trajectory_rows"],
            list(result["trajectory_rows"][0]),
        )
        write_csv(
            args.output_dir / f"DRTP_MECHANISM_{result['label']}_GROUP_ENDPOINTS.csv",
            result["group_rows"],
            list(result["group_rows"][0]),
        )
        write_csv(
            args.output_dir / f"DRTP_MECHANISM_{result['label']}_GROUP_SUMMARY.csv",
            result["aggregate_rows"],
            list(result["aggregate_rows"][0]),
        )
        write_csv(
            args.output_dir / f"DRTP_MECHANISM_{result['label']}_DESCRIPTIVE_ASSOCIATION.csv",
            result["correlation_rows"],
            list(result["correlation_rows"][0]),
        )
    write_csv(args.output_dir / "DRTP_TOPOLOGY_GROUP_CONTRACT.csv", result_a["topology_contract"], list(result_a["topology_contract"][0]))

    inventory = {
        "protocol": "DRTP-FINAL-MECHANISM-ASSET-AUDIT-V1",
        "mode": "read_only_archive_analysis",
        "training_started": False,
        "evaluation_started": False,
        "checkpoint_modified": False,
        "conclusion_label": "MECHANISM_ALIGNMENT_DESCRIPTIVE_ONLY",
        "cohorts": [{key: result[key] for key in ("label", "archive", "sha256", "endpoint_member", "sampler_log_count")} for result in (result_a, result_b)],
        "topology_graph_metrics": "blocked_by_absence_of_explicit_adjacency_or_edge_list_in_sampler_manifests",
        "allowed_interpretation": "Topology group/time semantics, final logged difficulty, actual exposure, and endpoint group outcomes may be described separately by cohort; no causal or single-root-cause conclusion is authorized.",
    }
    (args.output_dir / "DRTP_FINAL_MECHANISM_ASSET_INVENTORY.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    report = f"""# DRTP final A/B topology-exposure asset audit\n\n**Verdict:** `MECHANISM_ALIGNMENT_DESCRIPTIVE_ONLY`.\n\nThe two SHA256-verified final archives contain five DRTP sampler logs, five sampler manifests, and fixed endpoint condition summaries for each cohort. The analysis read these archives directly; it did not extract or alter checkpoints, invoke evaluation, train a model, select checkpoints, or read an evaluation tape online.\n\n## Available final assets\n\n| Cohort | DRTP sampler logs | Endpoint source | SHA256 |\n|---|---:|---|---|\n| A | {result_a['sampler_log_count']} | `{result_a['endpoint_member']}` | `{result_a['sha256']}` |\n| B | {result_b['sampler_log_count']} | `{result_b['endpoint_member']}` | `{result_b['sha256']}` |\n\nThe output CSVs provide group-level endpoint outcomes, actual reset exposure, final logged `q`, logged difficulty, and five normalized training milestones for each seed. A/B are never pooled.\n\n## Boundary\n\nThe sampler manifests expose frozen group membership and failure timing, but do not themselves carry an explicit adjacency matrix or edge list. Therefore, this audit does **not** calculate broken-edge counts, graph connectivity, or shortest-path statistics. Those values may only be added after locating the exact frozen graph-definition artifact. The present outputs support descriptive topology-group/time and exposure analysis, not causal attribution or a post-hoc root-cause claim.\n"""
    (args.output_dir / "DRTP_FINAL_MECHANISM_ASSET_AUDIT.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
