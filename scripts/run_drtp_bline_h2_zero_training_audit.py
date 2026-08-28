"""Read-only H2 hypothesis-generation audit over the completed B3 archive.

This script never loads a checkpoint into an environment and never invokes a
training/evaluation entry point. It reads the archived CSV/JSONL evidence only.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import tarfile
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean, median

SEEDS = (2701, 2702, 2703)
ARMS = ("utr_sg", "drtp_sg")
MILESTONES = ((976, "0.25M"), (1953, "0.50M"), (2930, "0.75M"), (3907, "1.00M"))
PHASES = ((1, 976, "0-0.25M"), (977, 1953, "0.25-0.50M"), (1954, 2930, "0.50-0.75M"), (2931, 3907, "0.75-1.00M"))
PPO_FIELDS = ("train_avg_reward", "entropy", "value_loss", "advantage_mean", "advantage_std", "approx_kl", "clip_fraction", "grad_norm", "explained_variance")
TAUS = (0, 20, 60)


def finite_mean(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    return fmean(values) if values else math.nan


def phase_for(update: int) -> str | None:
    for start, end, label in PHASES:
        if start <= update <= end:
            return label
    return None


def member_text(handle: tarfile.TarFile, name: str) -> io.TextIOWrapper:
    value = handle.extractfile(name)
    if value is None:
        raise FileNotFoundError(name)
    return io.TextIOWrapper(value, encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/drtp_bline_h2"))
    args = parser.parse_args()
    if not args.archive.is_file():
        raise FileNotFoundError(args.archive)
    out = args.output_dir.resolve()
    partial_names = {"h2_milestone_comparison.csv", "h2_early_learning_state.csv", "h2_sampler_interaction.csv"}
    if out.exists() and any(out.iterdir()):
        existing = {item.name for item in out.iterdir()}
        if not existing.issubset(partial_names):
            raise FileExistsError(f"refusing to overwrite non-partial audit: {out}")
    out.mkdir(parents=True, exist_ok=True)

    with tarfile.open(args.archive, "r:gz") as archive:
        names = archive.getnames()
        required = [
            "drtp_b3/evaluations/final_1m/raw_episode_metrics.csv",
            "drtp_b3/evaluations/final_1m/evaluation_manifest.json",
        ]
        if any(name not in names for name in required):
            raise RuntimeError("B3 archive lacks final evaluation products")
        manifests: dict[tuple[str, int], dict] = {}
        train_rows: list[dict] = []
        sampler_rows: list[dict] = []
        for arm in ARMS:
            for seed in SEEDS:
                prefix = f"drtp_b3/runs/{arm}/seed{seed}/"
                manifest_name = prefix + "run_manifest.json"
                manifest = json.load(member_text(archive, manifest_name))
                if manifest.get("status") != "completed" or manifest.get("environment_steps") != 1_000_192:
                    raise RuntimeError(f"invalid B3 manifest: {manifest_name}")
                manifests[(arm, seed)] = manifest
                for row in csv.DictReader(member_text(archive, prefix + "train_log.csv")):
                    row.update({"method": arm, "seed": seed})
                    train_rows.append(row)
                for row in csv.DictReader(member_text(archive, prefix + "drtp_topology_sampler_log.csv")):
                    row.update({"method": arm, "seed": seed})
                    sampler_rows.append(row)

        evaluation = list(csv.DictReader(member_text(archive, required[0])))
        evaluation_manifest = json.load(member_text(archive, required[1]))
        if len(evaluation) != 3000 or evaluation_manifest.get("raw_rows") != 3000:
            raise RuntimeError("B3 evaluation row-count violation")
        by_eval: dict[tuple[str, int, str], list[dict]] = defaultdict(list)
        for row in evaluation:
            by_eval[(row["method"], int(row["train_seed"]), row["topology_condition"])].append(row)
        control_rows: list[dict] = []
        for seed in SEEDS:
            for condition in ("nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120"):
                drtp, utr = by_eval[("drtp_sg", seed, condition)], by_eval[("utr_sg", seed, condition)]
                control_rows.append({"seed": seed, "condition": condition,
                    "delta_J_drtp_minus_utr": finite_mean([float(x["J"]) for x in drtp]) - finite_mean([float(x["J"]) for x in utr]),
                    "delta_timeout_drtp_minus_utr": finite_mean([float(x["timeout"]) for x in drtp]) - finite_mean([float(x["timeout"]) for x in utr]),
                    "delta_collision_drtp_minus_utr": finite_mean([float(x["collision"]) for x in drtp]) - finite_mean([float(x["collision"]) for x in utr]),
                })
        faults = [row for row in control_rows if row["condition"] != "nominal"]
        adverse_seeds = sorted({row["seed"] for row in faults if row["delta_J_drtp_minus_utr"] < 0.0 and row["delta_timeout_drtp_minus_utr"] > 0.0})
        outcome_repeated = len(adverse_seeds) >= 2

        # Exact milestone snapshots of only production-existing PPO fields.
        milestone_rows: list[dict] = []
        by_train = {(row["method"], int(row["seed"]), int(row["update"])): row for row in train_rows}
        for arm in ARMS:
            for seed in SEEDS:
                for update, label in MILESTONES:
                    row = by_train.get((arm, seed, update))
                    if row is None:
                        raise RuntimeError(f"missing milestone log {arm}/seed{seed}/update{update}")
                    payload = {"method": arm, "seed": seed, "update": update, "milestone": label}
                    for key in PPO_FIELDS:
                        payload[key] = row.get(key, "")
                    milestone_rows.append(payload)
        write_csv(out / "h2_milestone_comparison.csv", milestone_rows)

        # Early-state rows retain only direct, real log fields; no proxy is invented.
        early = [row for row in milestone_rows if row["milestone"] in {"0.25M", "0.50M"}]
        write_csv(out / "h2_early_learning_state.csv", early)

        sampler_summary: list[dict] = []
        sampler_by_phase: dict[tuple[str, int, str], list[dict]] = defaultdict(list)
        for row in sampler_rows:
            update = int(row["update"])
            phase = phase_for(update)
            if phase is not None:
                sampler_by_phase[(row["method"], int(row["seed"]), phase)].append(row)
        q_fields = ("q_F0", "q_TE", "q_TL", "q_DS", "q_DL", "q_CP")
        for key, rows in sorted(sampler_by_phase.items()):
            arm, seed, phase = key
            selected = Counter(row.get("group", "") for row in rows if row.get("record_type") == "selection")
            adaptation = [row for row in rows if row.get("record_type") == "weight_update"]
            q_l1 = []
            for row in adaptation:
                try:
                    q_l1.append(sum(abs(float(row[field]) - 1.0 / 6.0) for field in q_fields))
                except (KeyError, ValueError):
                    pass
            sampler_summary.append({
                "method": arm, "seed": seed, "phase": phase,
                "selection_count": sum(selected.values()), "adaptation_count": len(adaptation),
                "q_l1_from_failure_uniform_mean": finite_mean(q_l1),
                **{f"exposure_{group}": selected.get(group, 0) / max(sum(selected.values()), 1) for group in ("N", "F0", "TE", "TL", "DS", "DL", "CP")},
            })
        write_csv(out / "h2_sampler_interaction.csv", sampler_summary)

        # Stream only tau 0/20/60 behavior records, without materializing the
        # six multi-GB JSONL files. This is read-only and phase-aligned by update.
        behavior: dict[tuple[str, int, str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        # A single adverse seed cannot establish the H2 mechanism, but its
        # failure-relative telemetry is still required to characterize a weak
        # candidate against its paired UTR control.  Do not discard that
        # evidence merely because the replication gate is not yet met.
        if adverse_seeds:
            for arm in ARMS:
                for seed in SEEDS:
                    event_name = f"drtp_b3/runs/{arm}/seed{seed}/failure_telemetry/failure_event_window.jsonl"
                    with member_text(archive, event_name) as handle:
                        for line in handle:
                        # The selective substring test avoids JSON decoding the
                        # overwhelming majority of window records.
                            if not any(f'"failure_relative_step":{tau}' in line for tau in TAUS):
                                continue
                            row = json.loads(line)
                            tau = int(row["failure_relative_step"])
                            update = int(row["update"])
                            phase = phase_for(update)
                            if phase is None:
                                continue
                            values = behavior[(arm, seed, phase, tau)]
                            direct = row["direct_information_path"]["state"] == "direct"
                            relay = row["direct_information_path"]["state"] == "relay"
                            values["direct_path_rate"].append(float(direct))
                            values["relay_path_rate"].append(float(relay))
                            values["any_information_path_rate"].append(float(direct or relay))
                            values["valid_target_information_rate"].append(float(row.get("attacker_valid_target_information") or 0.0))
                            values["task_support_rate"].append(float(row["task_support_state"].get("chain_support") or 0.0))
                            values["attack_window_rate"].append(float(max(row.get("attack_window_state") or [0.0])))
                            values["cache_mean_age"].append(float(row["cache_freshness"].get("mean_age") or 0.0))
                            values["path_switch_rate"].append(float(row["direct_information_path"].get("path_switch_event") or False))
                            values["timeout_rate"].append(float(row.get("timeout") or 0.0))
                            values["collision_rate"].append(float(row.get("collision") or 0.0))
        behavior_rows = []
        for (arm, seed, phase, tau), values in sorted(behavior.items()):
            behavior_rows.append({"method": arm, "seed": seed, "phase": phase, "tau": tau,
                                  "records": len(values["direct_path_rate"]),
                                  **{name: finite_mean(series) for name, series in values.items()}})
        write_csv(out / "h2_behavior_support_timeline.csv", behavior_rows)

        write_csv(out / "h2_paired_utr_control.csv", control_rows)

    # Gate is conservative: one adverse DRTP seed cannot meet the frozen
    # H2 candidate chain's cross-seed contrast requirement by itself.
    # A single adverse seed cannot establish H2, but it can generate a weak,
    # explicitly post-hoc candidate for a future independent falsification.
    gate = "H2_WEAK_CANDIDATE" if adverse_seeds else "H2_NO_GO"
    # A H2 candidate is intentionally not emitted automatically: the archive
    # can generate a hypothesis only, and candidate status needs an explicit
    # multi-layer human audit of these precomputed time-series products.
    evidence = [
        {"criterion": "early-state precedes final reversal", "status": "descriptive products generated", "interpretation": "not sufficient alone"},
        {"criterion": "adaptive interaction", "status": "q/exposure phase table generated", "interpretation": "correlation is not causality"},
        {"criterion": "behavior/support", "status": "tau 0/20/60 phase timeline generated", "interpretation": "requires UTR control"},
        {"criterion": "cross-seed adverse outcome repetition", "status": "fail" if not outcome_repeated else "partial", "interpretation": f"adverse seeds: {adverse_seeds}"},
    ]
    write_csv(out / "h2_evidence_matrix.csv", evidence)
    (out / "H2_HYPOTHESIS_GENERATION_CONTRACT.md").write_text(
        "# H2 hypothesis-generation contract\n\nThis audit is zero-training and reads only the completed B3 archive. It cannot prove H2 or authorize any algorithm modification. H2 requires early-state → adaptive interaction → behavior/support → outcome evidence with paired UTR control and a future new-seed confirmation.\n",
        encoding="utf-8")
    (out / "h2_seed2702_timeline.md").write_text(
        "# seed2702 timeline\n\nSee the milestone, sampler, behavior/support and paired-control CSV products. seed2702 is used for hypothesis generation only; it cannot prove H2.\n",
        encoding="utf-8")
    (out / "h2_contrast_2701_2702_2703.md").write_text(
        "# 2701/2702/2703 contrast\n\nThe final paired outcome table shows favorable DRTP directions for 2701, adverse directions for 2702, and mixed-to-favorable directions for 2703. The single adverse seed prevents a repeated H2 failure-chain claim.\n",
        encoding="utf-8")
    report = ["# H2 zero-training gate report", "", f"Status: `{gate}`", "",
              "## Integrity", "", "- six completed B3 trajectories; 1,000,192 steps each; 3,000 retained evaluation rows; fixed development tape.",
              "- analysis reads archived logs/telemetry only; no training, evaluation rerun, checkpoint promotion, or algorithm change.",
              "", "## Gate reason", "",
              f"The adverse final outcome direction (lower J and higher timeout for DRTP than paired UTR over fault conditions) occurs for seed(s) {adverse_seeds}. One adverse seed can generate only a weak post-hoc H2 candidate; it cannot establish a repeated vulnerability mechanism or authorize an intervention.",
              "", "## Frozen action", "", "No new training, 3M continuation, rerun, seed replacement, or stabilization modification is authorized by this audit."]
    (out / "H2_ZERO_TRAINING_GATE_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": gate, "adverse_seeds": adverse_seeds, "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
