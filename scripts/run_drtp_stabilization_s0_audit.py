"""Freeze the two-shot DRTP stabilization S0 contract without training.

The audit deliberately ignores performance labels while selecting the DRTP-TR
L1 cap.  It reads only sampler state trajectories from pre-existing original
DRTP runs, derives the pooled P90 of actual post-projection q movements, and
uses existing same-checkpoint multi-tape cells only to quantify evaluation
variation.  It never launches an environment, evaluator, or optimizer.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import statistics
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "drtp_stabilization_s0"
FREEZE = ROOT / "configs" / "drtp_stabilization_s0_freeze.json"
Q_FIELDS = ("q_F0", "q_TE", "q_TL", "q_DS", "q_DL", "q_CP")

# Sources are selected solely by method/provenance availability.  They are
# intentionally not conditional on whether a seed later looked good or bad.
DIRECT_SOURCES = (
    ROOT / "artifacts" / "drtp_stab_a0" / "source_logs" / "results" / "development"
    / "drtp_sg_strict_continuous_10m" / "runs" / "drtp_sg" / "seed1901" / "drtp_topology_sampler_log.csv",
    ROOT / "artifacts" / "drtp_stab_a0" / "source_logs" / "results" / "development"
    / "drtp_sg_strict_continuous_10m" / "runs" / "drtp_sg" / "seed1902" / "drtp_topology_sampler_log.csv",
    ROOT / "artifacts" / "drtp_stab_a0" / "source_logs" / "results" / "heldout"
    / "drtp_sg_heldout_v2" / "runs" / "drtp_sg" / "seed2001" / "drtp_topology_sampler_log.csv",
    ROOT / "artifacts" / "drtp_stab_a0" / "source_logs" / "results" / "heldout"
    / "drtp_sg_heldout_v2" / "runs" / "drtp_sg" / "seed2002" / "drtp_topology_sampler_log.csv",
    ROOT / "artifacts" / "drtp_stab_a0" / "source_logs" / "results" / "heldout"
    / "drtp_sg_heldout_v2" / "runs" / "drtp_sg" / "seed2003" / "drtp_topology_sampler_log.csv",
)
ARCHIVE_SOURCES = (
    (Path("D:/File/Downloads/drtp_utr_q2_paired_5seed_cloud_10way.tar.gz"),
     "results/formal/drtp_utr_q2_paired_5seed_cloud_10way/runs/drtp_sg/seed"),
    (Path("D:/File/Downloads/drtp_b3_1m_results.tar.gz"), "drtp_b3/runs/drtp_sg/seed"),
    (Path("D:/File/Downloads/drtp_h2_confirmation_stage1_05m_results.tar.gz"),
     "results/development/drtp_h2_confirmation_stage1/runs/drtp_sg/seed"),
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("empty percentile input")
    ranked = sorted(values)
    position = (len(ranked) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ranked[lower]
    return ranked[lower] + (ranked[upper] - ranked[lower]) * (position - lower)


def parse_updates(payload: bytes, source: str) -> tuple[list[dict], list[float]]:
    rows = csv.DictReader(io.StringIO(payload.decode("utf-8")))
    previous: tuple[float, ...] | None = None
    audit_rows, movements = [], []
    for row in rows:
        if row.get("record_type") != "weight_update" or str(row.get("adapted")).lower() != "true":
            continue
        try:
            q = tuple(float(row[field]) for field in Q_FIELDS)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid adapted q row in {source}") from exc
        if not math.isclose(sum(q), 1.0, abs_tol=1e-9) or any(value < .05 - 1e-10 or value > .35 + 1e-10 for value in q):
            raise ValueError(f"invalid projected q in {source}")
        if previous is not None:
            l1 = sum(abs(left - right) for left, right in zip(q, previous))
            movements.append(l1)
            audit_rows.append({"source": source, "update": int(row["update"]), "adaptation_count": int(row["adaptation_count"]),
                               "q_step_l1": l1, **{field: value for field, value in zip(Q_FIELDS, q)}})
        previous = q
    return audit_rows, movements


def read_sources() -> tuple[list[dict], list[float], list[dict]]:
    audit_rows: list[dict] = []
    movements: list[float] = []
    inventory: list[dict] = []
    for path in DIRECT_SOURCES:
        if not path.exists():
            inventory.append({"source": str(path), "status": "missing", "origin": "direct"})
            continue
        payload = path.read_bytes()
        rows, values = parse_updates(payload, str(path.relative_to(ROOT)))
        audit_rows.extend(rows); movements.extend(values)
        inventory.append({"source": str(path.relative_to(ROOT)), "status": "included", "origin": "direct",
                          "sha256": sha256_bytes(payload), "adapted_movement_count": len(values)})
    for archive, prefix in ARCHIVE_SOURCES:
        if not archive.exists():
            inventory.append({"source": str(archive), "status": "missing", "origin": "archive"})
            continue
        with tarfile.open(archive, "r:gz") as bundle:
            names = sorted(name for name in bundle.getnames()
                           if name.startswith(prefix) and name.endswith("/drtp_topology_sampler_log.csv"))
            for name in names:
                member = bundle.extractfile(name)
                if member is None:
                    raise ValueError(f"cannot extract {name}")
                payload = member.read()
                label = f"{archive.name}:{name}"
                rows, values = parse_updates(payload, label)
                audit_rows.extend(rows); movements.extend(values)
                inventory.append({"source": label, "status": "included", "origin": "archive",
                                  "sha256": sha256_bytes(payload), "adapted_movement_count": len(values)})
    return audit_rows, movements, inventory


def evaluation_noise() -> dict:
    path = ROOT / "artifacts" / "drtp_reliability_a0" / "rel_a0_decision.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    grouped: dict[tuple[str, int, str], dict[str, float]] = defaultdict(dict)
    for cell in payload["cell_summary"]:
        grouped[(cell["method"], int(cell["training_seed"]), cell["tape"])][cell["condition"]] = float(cell["J"])
    per_checkpoint: list[dict] = []
    deviations, pairwise = [], []
    for (method, seed, tape), conditions in sorted(grouped.items()):
        required = ("f0", "timing", "duration", "compound")
        if not all(condition in conditions for condition in required):
            continue
        per_checkpoint.append({"method": method, "seed": seed, "tape": tape,
                               "J_pert_mean": statistics.fmean(conditions[c] for c in required)})
    by_checkpoint: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in per_checkpoint:
        by_checkpoint[(row["method"], row["seed"])].append(row["J_pert_mean"])
    for key, values in by_checkpoint.items():
        median = statistics.median(values)
        deviations.extend(abs(value - median) for value in values)
        pairwise.extend(abs(left - right) for index, left in enumerate(values) for right in values[index + 1:])
    epsilon = percentile(pairwise, .90)
    return {"source": str(path.relative_to(ROOT)), "source_sha256": sha256_bytes(path.read_bytes()),
            "endpoint": "J_pert_mean = mean(J_f0, J_timing, J_duration, J_compound)",
            "checkpoint_tape_cells": per_checkpoint, "checkpoint_count": len(by_checkpoint),
            "paired_tape_difference_count": len(pairwise), "P50_abs_paired_difference": percentile(pairwise, .50),
            "P90_abs_paired_difference": epsilon, "P95_abs_paired_difference": percentile(pairwise, .95),
            "P90_abs_deviation_from_checkpoint_tape_median": percentile(deviations, .90),
            "epsilon_J": epsilon,
            "definition": "P90 of absolute pairwise same-checkpoint cross-tape differences; this is evaluation-tape variation, not training-cohort variation."}


def replay(rows: Iterable[dict], delta: float) -> dict:
    # Each row encodes an observed original DRTP target after its bounded-simplex
    # projection.  The convex L1 clip below is the frozen TR rule.  Convexity
    # preserves q mass and floor/cap; no post-TR projection is applied.
    by_source: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_source[row["source"]].append(row)
    summary, violations = [], []
    for source, source_rows in sorted(by_source.items()):
        # This is a forced-target replay: original post-projection q targets
        # are replayed through TR.  It verifies the cap's exact algebra but
        # cannot represent counterfactual returns/exposure during training.
        tr_q = [1.0 / len(Q_FIELDS)] * len(Q_FIELDS)
        activated, max_final_l1, floor_cap_failures, simplex_failures = 0, 0.0, 0, 0
        for row in source_rows:
            target = [float(row[field]) for field in Q_FIELDS]
            raw_l1 = sum(abs(left - right) for left, right in zip(target, tr_q))
            scale = 1.0 if raw_l1 <= delta else delta / raw_l1
            if scale < 1.0:
                activated += 1
            next_q = [left + scale * (right - left) for left, right in zip(tr_q, target)]
            final_l1 = sum(abs(left - right) for left, right in zip(next_q, tr_q))
            max_final_l1 = max(max_final_l1, final_l1)
            simplex_failures += not math.isclose(sum(next_q), 1.0, abs_tol=1e-10)
            floor_cap_failures += any(value < .05 - 1e-12 or value > .35 + 1e-12 for value in next_q)
            if final_l1 > delta + 1e-10:
                violations.append({"source": source, "update": row["update"], "final_l1": final_l1})
            tr_q = next_q
        summary.append({"source": source, "updates": len(source_rows), "activation_count": activated,
                        "activation_rate": activated / len(source_rows) if source_rows else 0.0,
                        "max_observed_l1": max(row["q_step_l1"] for row in source_rows),
                        "max_tr_final_l1": max_final_l1, "simplex_failures": simplex_failures,
                        "floor_cap_failures": floor_cap_failures})
    return {"per_source": summary, "l1_bound_violations": len(violations),
            "global_activation_rate": sum(item["activation_count"] for item in summary) / max(1, sum(item["updates"] for item in summary)),
            "all_simplex_and_floor_cap_checks_pass": all(not item["simplex_failures"] and not item["floor_cap_failures"] for item in summary)}


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    updates, movements, inventory = read_sources()
    if len(movements) < 100:
        raise SystemExit("S0_NOT_READY: insufficient valid original-DRTP adapted boundaries")
    delta = percentile(movements, .90)
    noise = evaluation_noise()
    offline = replay(updates, delta)
    source_hash = sha256_bytes(Path(__file__).read_bytes())
    freeze = {
        "protocol": "DRTP-STABILIZATION-S0-V1", "training_started": False, "evaluation_rerun_started": False,
        "selection_rule": "label-free pooled P90 of final post-projection original-DRTP q movement",
        "delta_q_l1": delta, "delta_statistics": {"n": len(movements), "P50": percentile(movements, .50),
            "P75": percentile(movements, .75), "P90": delta, "P95": percentile(movements, .95), "max": max(movements)},
        "epsilon_J": noise["epsilon_J"], "epsilon_J_definition": noise["definition"],
        "practical_downside_improvement_margin": noise["epsilon_J"],
        "s2_uniform_anchor": .20, "s2_adaptive_mass": .80,
        "source_script_sha256": source_hash,
        "source_inventory": inventory,
        "offline_replay": offline,
    }
    FREEZE.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(OUT / "s0_q_update_movements.csv", updates)
    write_csv(OUT / "s0_sampler_source_inventory.csv", inventory)
    write_csv(OUT / "s0_evaluation_tape_cells.csv", noise["checkpoint_tape_cells"])
    report = ["# S0 delta and evaluation-margin freeze", "", "Status: `S0_NUMERICAL_FREEZE_COMPLETE`", "",
              "## Label-free sampler rule", "", f"- Valid post-projection movement samples: `{len(movements)}`.",
              f"- `delta_q_l1 = pooled P90 = {delta:.12g}`.",
              f"- P50/P75/P95/max: `{freeze['delta_statistics']['P50']:.12g}` / `{freeze['delta_statistics']['P75']:.12g}` / `{freeze['delta_statistics']['P95']:.12g}` / `{freeze['delta_statistics']['max']:.12g}`.",
              "- Inclusion uses only original-DRTP sampler provenance; no good/bad, formal/independent outcome label is read by the selection rule.", "",
              "## Endpoint variation rule", "", f"- Primary robust endpoint: `{noise['endpoint']}`.",
              f"- Same-checkpoint cross-tape paired differences: `{noise['paired_tape_difference_count']}` from `{noise['checkpoint_count']}` checkpoints.",
              f"- `epsilon_J = P90(|J_tape_a - J_tape_b|) = {noise['epsilon_J']:.12g}`.",
              "- This bounds observed tape variation; it does not erase or pool training-cohort differences.", "",
              "## Frozen practical margins", "", f"- Practical downside-improvement margin: `{noise['epsilon_J']:.12g}` J units (strictly greater than this margin at the relevant gate).",
              "- S2 uniform anchor: `0.20`; adaptive mass: `0.80`.", "",
              "## Offline movement replay", "", "- Recorded original movements above the P90 cap: `10.00%` by construction.",
              f"- Forced-target TR replay activation: `{offline['global_activation_rate']:.2%}`; prior clipping can make later recorded targets farther from the candidate state.",
              "- The replay is a deterministic movement audit on recorded targets only; it does not simulate counterfactual policy learning or claim repair.", "",
              "## Inputs and reproducibility", "", "", f"- Audit script SHA256: `{source_hash}`.",
              "- Full source/member hashes and exclusion status: `s0_sampler_source_inventory.csv`.",
              "- Movement rows: `s0_q_update_movements.csv`; same-checkpoint tape cells: `s0_evaluation_tape_cells.csv`.", "",
              "No training, evaluator rerun, parameter sweep, or algorithm-selection result was executed in S0."]
    (OUT / "S0_DELTA_FREEZE_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": "S0_NUMERICAL_FREEZE_COMPLETE", "delta": delta, "epsilon_J": noise["epsilon_J"], "samples": len(movements)}, indent=2))


if __name__ == "__main__":
    main()
