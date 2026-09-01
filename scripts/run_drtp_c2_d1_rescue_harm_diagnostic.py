"""Zero-training C2-D1 rescue-versus-harm diagnostic.

The script intentionally consumes only archived C2 training artifacts.  It is
not a trainer, evaluator, selector, or threshold search.  Completed C2 endpoint
labels are retrospective labels only and never become online features.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Iterable


GROUPS = ("F0", "TE", "TL", "DS", "DL", "CP")
PHASES = {
    "early": (2, 488),
    "middle": (489, 976),
    "late": (977, 1953),
}
RESCUE = {4802, 4807, 4809}
HARM = {4804, 4805, 4806, 4808, 4810}
NEUTRAL = {4801, 4803}


def f(value: str | None) -> float | None:
    try:
        result = float(value or "")
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def avg(values: Iterable[float | None]) -> float | None:
    finite = [value for value in values if value is not None and math.isfinite(value)]
    return mean(finite) if finite else None


def fmt(value: float | None, digits: int = 4) -> str:
    return "NA" if value is None else f"{value:.{digits}f}"


def cohort(seed: int) -> str:
    return "A" if seed <= 4805 else "B"


def label(seed: int) -> str:
    if seed in RESCUE:
        return "rescue"
    if seed in HARM:
        return "harm"
    if seed in NEUTRAL:
        return "neutral_mixed"
    raise ValueError(f"unregistered seed: {seed}")


def top_group(row: dict[str, str], prefix: str) -> str | None:
    values = {group: f(row.get(f"{prefix}{group}")) for group in GROUPS}
    if any(value is None for value in values.values()):
        return None
    maximum = max(values.values())
    winners = [group for group, value in values.items() if value == maximum]
    return winners[0] if len(winners) == 1 else None


def phase_rows(rows: list[dict[str, str]], bounds: tuple[int, int]) -> list[dict[str, str]]:
    low, high = bounds
    return [row for row in rows if low <= int(row["update"]) <= high]


def summarize_phase(rows: list[dict[str, str]]) -> dict[str, object]:
    if not rows:
        raise RuntimeError("empty frozen phase")
    result: dict[str, object] = {"updates": len(rows)}
    for group in GROUPS:
        for source, target in (
            ("group_td_abs_", "td_abs"),
            ("group_weight_lagged_score_", "lagged_score"),
            ("group_weight_", "weight"),
            ("post_surrogate_", "post_surrogate"),
        ):
            result[f"{target}_{group}"] = avg(f(row.get(f"{source}{group}")) for row in rows)
    for column in (
        "advantage_mean", "advantage_std", "policy_loss", "value_loss",
        "approx_kl", "post_update_actor_kl", "clip_fraction", "grad_norm",
        "entropy", "train_avg_reward",
    ):
        result[column] = avg(f(row.get(column)) for row in rows)

    active = [row for row in rows if (f(row.get("group_weight_active_count")) or 0) > 0]
    result["active_weight_row_fraction"] = len(active) / len(rows)
    score_tops = [top_group(row, "group_weight_lagged_score_") for row in active]
    weight_tops = [top_group(row, "group_weight_") for row in active]
    aligned = [s == w for s, w in zip(score_tops, weight_tops) if s is not None and w is not None]
    result["score_weight_top_alignment"] = mean(aligned) if aligned else None
    result["score_rank_switch_rate"] = switch_rate(score_tops)
    result["weight_rank_switch_rate"] = switch_rate(weight_tops)
    result["score_top_group"] = majority(score_tops)
    result["weight_top_group"] = majority(weight_tops)

    weights = [f(row.get(f"group_weight_{group}")) for row in active for group in GROUPS]
    result["weight_floor_contact_fraction"] = mean(value <= 0.7500001 for value in weights if value is not None) if weights else None
    result["weight_cap_contact_fraction"] = mean(value >= 1.2499999 for value in weights if value is not None) if weights else None
    concentrations: list[float] = []
    for row in active:
        values = [abs(f(row.get(f"post_surrogate_{group}")) or 0.0) for group in GROUPS]
        total = sum(values)
        if total > 0:
            concentrations.append(max(values) / total)
    result["surrogate_concentration"] = avg(concentrations)
    return result


def majority(values: Iterable[str | None]) -> str | None:
    available = [value for value in values if value is not None]
    if not available:
        return None
    counts = Counter(available)
    maximum = max(counts.values())
    winners = sorted(key for key, count in counts.items() if count == maximum)
    return winners[0] if len(winners) == 1 else None


def switch_rate(values: list[str | None]) -> float | None:
    available = [value for value in values if value is not None]
    if len(available) < 2:
        return None
    return sum(left != right for left, right in zip(available, available[1:])) / (len(available) - 1)


def group_mean(records: list[dict[str, object]], key: str) -> float | None:
    return avg(record[key] if isinstance(record[key], float) else None for record in records)


def report_table(records: list[dict[str, object]], phase: str, category: str) -> dict[str, object]:
    chosen = [record for record in records if record["phase"] == phase and record["label"] == category]
    out: dict[str, object] = {"n": len(chosen)}
    keys = [
        "score_weight_top_alignment", "score_rank_switch_rate", "weight_rank_switch_rate",
        "weight_floor_contact_fraction", "weight_cap_contact_fraction", "surrogate_concentration",
        "advantage_mean", "advantage_std", "policy_loss", "value_loss", "approx_kl",
        "post_update_actor_kl", "clip_fraction", "grad_norm", "entropy", "train_avg_reward",
    ]
    for key in keys:
        out[key] = group_mean(chosen, key)
    for group in GROUPS:
        for prefix in ("td_abs", "lagged_score", "weight", "post_surrogate"):
            out[f"{prefix}_{group}"] = group_mean(chosen, f"{prefix}_{group}")
    return out


def direction(rescue: float | None, harm: float | None) -> str:
    if rescue is None or harm is None:
        return "not_identifiable"
    delta = rescue - harm
    if abs(delta) < 1e-12:
        return "equal"
    return "rescue_higher" if delta > 0 else "rescue_lower"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join("---" for _ in headers) + " |"
    return "\n".join([line, rule] + ["| " + " | ".join(row) + " |" for row in rows])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True, help="extracted drtp_c2_group_weighted_ppo_pilot directory")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    source = args.results_root.resolve()
    decision_path = source / "diagnostics" / "c2_group_weighted_ppo_gate" / "C2_GATE_DECISION.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    if decision.get("verdict") != "C2_NO_GO":
        raise RuntimeError("D1 only accepts the completed frozen C2_NO_GO archive")
    args.output_dir.mkdir(parents=True, exist_ok=False)

    records: list[dict[str, object]] = []
    artifact_ledger: list[dict[str, object]] = []
    for seed in range(4801, 4811):
        run = source / "runs" / "group_weighted_utr_sg" / f"seed{seed}"
        log = run / "train_log.csv"
        if not log.exists():
            raise RuntimeError(f"missing frozen candidate log: {log}")
        with log.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        updates = [int(row["update"]) for row in rows]
        if updates != list(range(1, 1954)):
            raise RuntimeError(f"unexpected update ledger for seed {seed}")
        artifact_ledger.append({
            "seed": seed, "cohort": cohort(seed), "label": label(seed), "train_log": str(log),
            "updates": len(rows), "runtime_state_250k": (run / "actor_critic_runtime_state_milestone_250k.pt").exists(),
            "runtime_state_500k": (run / "actor_critic_runtime_state_milestone_500k.pt").exists(),
            "per_group_gradient_tensor": False,
            "per_group_advantage_samples": False,
            "role_policy_distribution": False,
            "training_behavior_telemetry": False,
        })
        for phase, bounds in PHASES.items():
            record = {"seed": seed, "cohort": cohort(seed), "label": label(seed), "phase": phase}
            record.update(summarize_phase(phase_rows(rows, bounds)))
            records.append(record)

    output = args.output_dir
    with (output / "C2_D1_RESCUE_HARM_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(artifact_ledger[0]))
        writer.writeheader(); writer.writerows(artifact_ledger)
    with (output / "C2_D1_PHASE_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)

    summaries: dict[str, dict[str, dict[str, object]]] = {}
    for phase in PHASES:
        summaries[phase] = {category: report_table(records, phase, category) for category in ("rescue", "harm", "neutral_mixed")}

    group_rows: list[list[str]] = []
    for phase in PHASES:
        rescue_summary, harm_summary = summaries[phase]["rescue"], summaries[phase]["harm"]
        for group in GROUPS:
            group_rows.append([
                phase, group,
                fmt(rescue_summary[f"lagged_score_{group}"]), fmt(harm_summary[f"lagged_score_{group}"]),
                direction(rescue_summary[f"lagged_score_{group}"], harm_summary[f"lagged_score_{group}"]),
                fmt(rescue_summary[f"weight_{group}"]), fmt(harm_summary[f"weight_{group}"]),
                direction(rescue_summary[f"weight_{group}"], harm_summary[f"weight_{group}"]),
            ])
    (output / "C2_D1_GROUP_SCORE_ANALYSIS.md").write_text(
        "# C2-D1 group-score analysis\n\n"
        "Training-only, descriptive rescue-versus-harm summaries. Outcome labels were not read by the training runs.\n\n" +
        markdown_table(["Phase", "Group", "Rescue lagged score", "Harm lagged score", "Direction", "Rescue weight", "Harm weight", "Direction"], group_rows) + "\n",
        encoding="utf-8")

    weight_rows: list[list[str]] = []
    loss_rows: list[list[str]] = []
    temporal_rows: list[list[str]] = []
    for phase in PHASES:
        rescue_summary, harm_summary = summaries[phase]["rescue"], summaries[phase]["harm"]
        weight_rows.append([phase, str(rescue_summary["n"]), str(harm_summary["n"]), fmt(rescue_summary["score_weight_top_alignment"]), fmt(harm_summary["score_weight_top_alignment"]), fmt(rescue_summary["weight_rank_switch_rate"]), fmt(harm_summary["weight_rank_switch_rate"]), fmt(rescue_summary["weight_floor_contact_fraction"]), fmt(harm_summary["weight_floor_contact_fraction"]), fmt(rescue_summary["weight_cap_contact_fraction"]), fmt(harm_summary["weight_cap_contact_fraction"])])
        loss_rows.append([phase, fmt(rescue_summary["advantage_mean"]), fmt(harm_summary["advantage_mean"]), fmt(rescue_summary["advantage_std"]), fmt(harm_summary["advantage_std"]), fmt(rescue_summary["surrogate_concentration"]), fmt(harm_summary["surrogate_concentration"]), fmt(rescue_summary["post_update_actor_kl"]), fmt(harm_summary["post_update_actor_kl"])])
        temporal_rows.append([phase, "before terminal evaluation" if phase != "late" else "late descriptive only", fmt(rescue_summary["train_avg_reward"]), fmt(harm_summary["train_avg_reward"]), direction(rescue_summary["train_avg_reward"], harm_summary["train_avg_reward"]), fmt(rescue_summary["advantage_std"]), fmt(harm_summary["advantage_std"]), direction(rescue_summary["advantage_std"], harm_summary["advantage_std"])])

    (output / "C2_D1_WEIGHT_DYNAMICS.md").write_text(
        "# C2-D1 applied-weight dynamics\n\n"
        "All values are training-only phase means. Contact fractions use the frozen [0.75, 1.25] bounds and are descriptive, not tuning targets.\n\n" +
        markdown_table(["Phase", "Rescue n", "Harm n", "Rescue score-weight alignment", "Harm alignment", "Rescue weight-rank switching", "Harm switching", "Rescue floor contact", "Harm floor contact", "Rescue cap contact", "Harm cap contact"], weight_rows) + "\n",
        encoding="utf-8")
    (output / "C2_D1_ADVANTAGE_LOSS_ANALYSIS.md").write_text(
        "# C2-D1 advantage and actor-loss analysis\n\n"
        "The archive stores aggregate advantage moments and post-update per-group surrogate values, but not per-group advantage samples, signs, medians, or exact per-group actor-loss contributions. Direct groupwise advantage-sign analysis is therefore not identifiable.\n\n" +
        markdown_table(["Phase", "Rescue advantage mean", "Harm advantage mean", "Rescue advantage SD", "Harm advantage SD", "Rescue surrogate concentration", "Harm concentration", "Rescue post-update KL", "Harm post-update KL"], loss_rows) + "\n",
        encoding="utf-8")
    (output / "C2_D1_GRADIENT_CONFLICT_ANALYSIS.md").write_text(
        "# C2-D1 gradient-conflict analysis\n\n"
        "`GRADIENT_CONFLICT_NOT_IDENTIFIABLE_FROM_EXISTING_C2_ARTIFACTS`\n\n"
        "The archive contains aggregate gradient/PPO telemetry but no saved per-group actor-gradient tensors or rollout buffers from which exact matched per-group gradients can be reconstructed. No rollout, checkpoint evaluation, or training was launched to fill that gap.\n",
        encoding="utf-8")
    (output / "C2_D1_POLICY_ROLE_ANALYSIS.md").write_text(
        "# C2-D1 policy and role analysis\n\n"
        "`ROLE_POLICY_AND_BEHAVIOR_NOT_IDENTIFIABLE_FROM_EXISTING_C2_ARTIFACTS`\n\n"
        "The C2 archive contains no role-conditioned action-probability time series, legal-path-use ledger, task-support behavior telemetry, or saved training trajectories. Consequently, role-specific policy collapse and coordination-geometry claims cannot be tested under the zero-training contract.\n",
        encoding="utf-8")
    (output / "C2_D1_TEMPORAL_PRECEDENCE_ANALYSIS.md").write_text(
        "# C2-D1 temporal-precedence analysis\n\n"
        "Early and middle windows occur before the final 0.5M checkpoint evaluation. They support only training-signal timing descriptions; the archive has no intermediate frozen performance evaluations, so temporal precedence over task-performance divergence is not identifiable.\n\n" +
        markdown_table(["Phase", "Timing status", "Rescue train reward", "Harm train reward", "Direction", "Rescue advantage SD", "Harm advantage SD", "Direction"], temporal_rows) + "\n",
        encoding="utf-8")

    # A C2-D1 candidate requires both cohorts to have at least two rescue seeds.
    # Cohort A has exactly one rescue by the frozen ledger, so a cross-cohort
    # repeatable mechanism cannot be established from C2 alone.
    cohort_counts = {name: {kind: sum(1 for seed in range(4801, 4811) if cohort(seed) == name and label(seed) == kind) for kind in ("rescue", "harm", "neutral_mixed")} for name in ("A", "B")}
    early_same_direction = []
    for metric in ("score_weight_top_alignment", "weight_rank_switch_rate", "surrogate_concentration", "advantage_std", "post_update_actor_kl"):
        by_cohort: dict[str, str] = {}
        for name in ("A", "B"):
            subset = [record for record in records if record["phase"] == "early" and record["cohort"] == name]
            by_cohort[name] = direction(group_mean([r for r in subset if r["label"] == "rescue"], metric), group_mean([r for r in subset if r["label"] == "harm"], metric))
        early_same_direction.append({"metric": metric, "cohort_A": by_cohort["A"], "cohort_B": by_cohort["B"], "same_direction": by_cohort["A"] == by_cohort["B"] and by_cohort["A"] not in {"equal", "not_identifiable"}})
    repeated_direction = [item for item in early_same_direction if item["same_direction"]]
    verdict = "D1_INCONCLUSIVE" if repeated_direction else "D1_NO_ACTIONABLE_MECHANISM"
    rationale = (
        "At least one training-only early descriptive direction matched across cohorts, but Cohort A contains only one frozen rescue seed and key group-gradient, group-advantage, role-policy, and intermediate-performance layers are absent. The archive cannot establish a repeatable, temporally leading actionable mechanism."
        if repeated_direction else
        "No predeclared aggregate training-only metric showed the same nonzero rescue-versus-harm direction in both cohorts. Together with the missing group-gradient, group-advantage, role-policy, and intermediate-performance layers, the archive does not identify an actionable mechanism."
    )
    final = {
        "protocol": "C2-D1-RESCUE-VS-HARM-ZERO-TRAINING-V1",
        "source_verdict": decision["verdict"],
        "verdict": verdict,
        "archive_integrity": True,
        "training_started": False,
        "evaluation_started": False,
        "mainline_a_modified": False,
        "seed_counts": cohort_counts,
        "early_cross_cohort_direction_checks": early_same_direction,
        "artifact_limitations": {
            "per_group_gradient_tensor": False,
            "per_group_advantage_samples": False,
            "role_policy_distribution": False,
            "training_behavior_telemetry": False,
            "intermediate_frozen_performance": False,
        },
        "rationale": rationale,
        "automatic_continuation_authorized": False,
    }
    (output / "C2_D1_DIAGNOSTIC.json").write_text(json.dumps({"final": final, "phase_summaries": summaries, "records": records}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "C2_D1_FINAL_VERDICT.md").write_text(
        "# C2-D1 final verdict\n\n"
        f"`{verdict}`\n\n{rationale}\n\n"
        "No new rollout, evaluation, continuation, weight adjustment, seed replacement, or Mainline-A modification was performed. This result does not authorize D2 or a new algorithm.\n",
        encoding="utf-8")
    print(json.dumps({"verdict": verdict, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
