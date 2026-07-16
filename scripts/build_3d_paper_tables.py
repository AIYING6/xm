from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECOVERY = ROOT / "results" / "intercept_3d_node_failure_recovery_summary.csv"
DEFAULT_FORMAL = ROOT / "results" / "intercept_3d_topology_curriculum_formal_summary.csv"
DEFAULT_TASK_SUPPORT_ABLATION = ROOT / "results" / "intercept_3d_task_support_ablation_formal_summary.csv"
DEFAULT_ROLE_PAIR_GATE_ABLATION = ROOT / "results" / "intercept_3d_role_pair_gate_ablation_formal_scale_matched_summary.csv"
DEFAULT_STRICT_SENSING_RECOVERY = (
    ROOT / "results" / "intercept_3d_strict_sensing_curriculum_seed0_pilot" / "formal_recovery_summary.csv"
)
DEFAULT_OUT_CSV = ROOT / "results" / "intercept_3d_paper_main_table.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "intercept_3d_paper_main_table.md"
DEFAULT_OUT_TEX = ROOT / "docs" / "intercept_3d_paper_main_table.tex"

SCENARIO_LABELS = {
    "relay_failure": "Relay failure",
    "scout_failure": "Scout failure",
    "dropout_030": "Communication dropout 0.30",
    "delay_2": "Two-step message delay",
    "radar_025": "Radar dropout 0.25",
    "range_075": "Communication range 0.75",
}

SCENARIO_ROLES = {
    "relay_failure": "Main node-failure evidence",
    "scout_failure": "Supporting node-failure evidence",
    "dropout_030": "Communication robustness trend",
    "delay_2": "Communication robustness trend",
    "radar_025": "Sensing robustness trend",
    "range_075": "Stress / boundary case",
}

SCENARIO_ORDER = (
    "relay_failure",
    "scout_failure",
    "dropout_030",
    "delay_2",
    "radar_025",
    "range_075",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build paper-facing summary tables for the 3DOF topology-curriculum study.")
    parser.add_argument("--recovery-summary", type=Path, default=DEFAULT_RECOVERY)
    parser.add_argument("--formal-summary", type=Path, default=DEFAULT_FORMAL)
    parser.add_argument("--task-support-ablation", type=Path, default=DEFAULT_TASK_SUPPORT_ABLATION)
    parser.add_argument("--role-pair-gate-ablation", type=Path, default=DEFAULT_ROLE_PAIR_GATE_ABLATION)
    parser.add_argument("--strict-sensing-recovery", type=Path, default=DEFAULT_STRICT_SENSING_RECOVERY)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-tex", type=Path, default=DEFAULT_OUT_TEX)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def f(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    if value == "" or value.lower() == "nan":
        return None
    return float(value)


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{100.0 * value:.1f}"


def fmt_steps(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value:.1f}"


def fmt_delta_ci(value: float | None, lo: float | None, hi: float | None, scale: float = 1.0) -> str:
    if value is None or lo is None or hi is None:
        return "NA"
    return f"{scale * value:+.1f} [{scale * lo:+.1f}, {scale * hi:+.1f}]"


def is_ci_positive(lo: float | None, hi: float | None) -> bool:
    return lo is not None and hi is not None and lo > 0.0 and hi > 0.0


def is_ci_negative(lo: float | None, hi: float | None) -> bool:
    return lo is not None and hi is not None and lo < 0.0 and hi < 0.0


def status_for(scenario: str, formal: dict[str, str] | None, recovery: dict[str, str] | None) -> str:
    if scenario == "range_075":
        return "Mixed; keep as stress case"
    if recovery is not None:
        rec_positive = is_ci_positive(
            f(recovery, "delta_post_failure_chain_recovered_ci_low"),
            f(recovery, "delta_post_failure_chain_recovered_ci_high"),
        )
        rec_steps_lower = is_ci_negative(
            f(recovery, "delta_post_failure_chain_recovery_steps_ci_low"),
            f(recovery, "delta_post_failure_chain_recovery_steps_ci_high"),
        )
        if rec_positive and rec_steps_lower:
            return "Separated recovery evidence"
        if f(recovery, "delta_post_failure_chain_recovered_mean") is not None and f(
            recovery, "delta_post_failure_chain_recovered_mean"
        ) > 0.0:
            return "Positive trend; CI crosses zero"
    if formal is not None:
        success_lo = f(formal, "paired_delta_success_ci_low")
        success_hi = f(formal, "paired_delta_success_ci_high")
        success_delta = f(formal, "paired_delta_success_mean")
        steps_lo = f(formal, "paired_delta_steps_ci_low")
        steps_hi = f(formal, "paired_delta_steps_ci_high")
        steps_delta = f(formal, "paired_delta_steps_mean")
        if is_ci_positive(success_lo, success_hi) or is_ci_negative(steps_lo, steps_hi):
            return "Separated aggregate evidence"
        if (success_delta is not None and success_delta > 0.0) or (steps_delta is not None and steps_delta < 0.0):
            return "Positive trend; CI crosses zero"
    return "No positive claim"


def build_rows(formal_rows: list[dict[str, str]], recovery_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    formal_by_scenario = {row["scenario"]: row for row in formal_rows}
    recovery_by_scenario = {row["scenario"]: row for row in recovery_rows}
    rows: list[dict[str, str]] = []
    for scenario in SCENARIO_ORDER:
        formal = formal_by_scenario.get(scenario)
        recovery = recovery_by_scenario.get(scenario)
        if formal is None and recovery is None:
            continue
        source = recovery if recovery is not None else formal
        assert source is not None
        single_success = f(source, "single_success_mean")
        multi_success = f(source, "multi_success_mean")
        if recovery is not None:
            success_delta = f(recovery, "delta_success_mean")
            success_lo = f(recovery, "delta_success_ci_low")
            success_hi = f(recovery, "delta_success_ci_high")
            single_steps = f(recovery, "single_steps_mean")
            multi_steps = f(recovery, "multi_steps_mean")
            steps_delta = f(recovery, "delta_steps_mean")
            steps_lo = f(recovery, "delta_steps_ci_low")
            steps_hi = f(recovery, "delta_steps_ci_high")
        else:
            success_delta = f(formal, "paired_delta_success_mean") if formal is not None else None
            success_lo = f(formal, "paired_delta_success_ci_low") if formal is not None else None
            success_hi = f(formal, "paired_delta_success_ci_high") if formal is not None else None
            single_steps = f(formal, "single_steps_mean") if formal is not None else None
            multi_steps = f(formal, "multi_steps_mean") if formal is not None else None
            steps_delta = f(formal, "paired_delta_steps_mean") if formal is not None else None
            steps_lo = f(formal, "paired_delta_steps_ci_low") if formal is not None else None
            steps_hi = f(formal, "paired_delta_steps_ci_high") if formal is not None else None

        row = {
            "scenario": scenario,
            "label": SCENARIO_LABELS.get(scenario, scenario),
            "evidence_role": SCENARIO_ROLES.get(scenario, "Supporting evidence"),
            "paired_episodes": str(int(float(source["n_paired_episodes"]))),
            "single_success_percent": fmt_pct(single_success),
            "multi_success_percent": fmt_pct(multi_success),
            "success_delta_pp_ci95": fmt_delta_ci(success_delta, success_lo, success_hi, scale=100.0),
            "single_recovery_percent": "NA",
            "multi_recovery_percent": "NA",
            "recovery_delta_pp_ci95": "NA",
            "single_recovery_steps": "NA",
            "multi_recovery_steps": "NA",
            "recovery_steps_delta_ci95": "NA",
            "single_steps": fmt_steps(single_steps),
            "multi_steps": fmt_steps(multi_steps),
            "steps_delta_ci95": fmt_delta_ci(steps_delta, steps_lo, steps_hi),
            "claim_status": status_for(scenario, formal, recovery),
        }
        if recovery is not None:
            row["single_recovery_percent"] = fmt_pct(f(recovery, "single_post_failure_chain_recovered_mean"))
            row["multi_recovery_percent"] = fmt_pct(f(recovery, "multi_post_failure_chain_recovered_mean"))
            row["recovery_delta_pp_ci95"] = fmt_delta_ci(
                f(recovery, "delta_post_failure_chain_recovered_mean"),
                f(recovery, "delta_post_failure_chain_recovered_ci_low"),
                f(recovery, "delta_post_failure_chain_recovered_ci_high"),
                scale=100.0,
            )
            row["single_recovery_steps"] = fmt_steps(f(recovery, "single_post_failure_chain_recovery_steps_mean"))
            row["multi_recovery_steps"] = fmt_steps(f(recovery, "multi_post_failure_chain_recovery_steps_mean"))
            row["recovery_steps_delta_ci95"] = fmt_delta_ci(
                f(recovery, "delta_post_failure_chain_recovery_steps_mean"),
                f(recovery, "delta_post_failure_chain_recovery_steps_ci_low"),
                f(recovery, "delta_post_failure_chain_recovery_steps_ci_high"),
            )
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError("No rows generated")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def append_task_support_ablation(lines: list[str], path: Path) -> None:
    if not path.exists():
        return
    rows = read_csv(path)
    if not rows:
        return
    lines.extend(
        [
            "",
            "## Formal Task-Support Ablation",
            "",
            "Full multi-relation is compared against `no_task_support`; positive success/recovery deltas favor the full model, while negative step deltas favor the full model.",
            "",
            "| Scenario | N | Success full/no-task | Success delta pp [95% CI] | Recovery full/no-task | Recovery delta pp [95% CI] | Recovery-step delta [95% CI] |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['n_paired_episodes']} | "
            f"{100.0 * float(row['full_success_mean']):.1f} / {100.0 * float(row['no_task_support_success_mean']):.1f} | "
            f"{fmt_delta_ci(f(row, 'delta_success_mean'), f(row, 'delta_success_ci_low'), f(row, 'delta_success_ci_high'), scale=100.0)} | "
            f"{100.0 * float(row['full_post_failure_chain_recovered_mean']):.1f} / {100.0 * float(row['no_task_support_post_failure_chain_recovered_mean']):.1f} | "
            f"{fmt_delta_ci(f(row, 'delta_post_failure_chain_recovered_mean'), f(row, 'delta_post_failure_chain_recovered_ci_low'), f(row, 'delta_post_failure_chain_recovered_ci_high'), scale=100.0)} | "
            f"{fmt_delta_ci(f(row, 'delta_post_failure_chain_recovery_steps_mean'), f(row, 'delta_post_failure_chain_recovery_steps_ci_low'), f(row, 'delta_post_failure_chain_recovery_steps_ci_high'))} |"
        )


def append_role_pair_gate_ablation(lines: list[str], path: Path) -> None:
    if not path.exists():
        return
    rows = read_csv(path)
    if not rows:
        return
    lines.extend(
        [
            "",
            "## Formal Role-Pair Gate Ablation",
            "",
            "Full multi-relation is compared against `no_role_pair_gate`; this keeps relation channels but replaces the learned role-pair message gate with a scale-matched constant gate. Positive success/recovery deltas favor the full model, while negative step deltas favor the full model.",
            "",
            "| Scenario | N | Success full/no-gate | Success delta pp [95% CI] | Recovery full/no-gate | Recovery delta pp [95% CI] | Recovery-step delta [95% CI] |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['n_paired_episodes']} | "
            f"{100.0 * float(row['full_success_mean']):.1f} / {100.0 * float(row['no_role_pair_gate_success_mean']):.1f} | "
            f"{fmt_delta_ci(f(row, 'delta_success_mean'), f(row, 'delta_success_ci_low'), f(row, 'delta_success_ci_high'), scale=100.0)} | "
            f"{100.0 * float(row['full_post_failure_chain_recovered_mean']):.1f} / {100.0 * float(row['no_role_pair_gate_post_failure_chain_recovered_mean']):.1f} | "
            f"{fmt_delta_ci(f(row, 'delta_post_failure_chain_recovered_mean'), f(row, 'delta_post_failure_chain_recovered_ci_low'), f(row, 'delta_post_failure_chain_recovered_ci_high'), scale=100.0)} | "
            f"{fmt_delta_ci(f(row, 'delta_post_failure_chain_recovery_steps_mean'), f(row, 'delta_post_failure_chain_recovery_steps_ci_low'), f(row, 'delta_post_failure_chain_recovery_steps_ci_high'))} |"
        )


def strict_sensing_status(row: dict[str, str]) -> str:
    if is_ci_positive(
        f(row, "delta_post_failure_chain_recovered_ci_low"),
        f(row, "delta_post_failure_chain_recovered_ci_high"),
    ) and is_ci_negative(
        f(row, "delta_post_failure_chain_recovery_steps_ci_low"),
        f(row, "delta_post_failure_chain_recovery_steps_ci_high"),
    ):
        return "Separated strict-sensing recovery evidence"
    if f(row, "delta_post_failure_chain_recovered_mean") is not None and f(
        row, "delta_post_failure_chain_recovered_mean"
    ) > 0.0:
        return "Positive strict-sensing trend; CI crosses zero"
    return "No strict-sensing positive claim"


def append_strict_sensing_recovery(lines: list[str], path: Path) -> None:
    if not path.exists():
        return
    rows = read_csv(path)
    if not rows:
        return
    lines.extend(
        [
            "",
            "## Strict-Sensing Scenario-Depth Table",
            "",
            "This table uses the opt-in `--strict-target-sensing` setting, where local observations, shared observations, and graph target nodes do not fall back to true target state before a valid detection. The checkpoints are a budget-labeled scenario-depth pilot: existing node-failure curriculum checkpoints were fine-tuned for 10 PPO updates under strict sensing, then evaluated with 30 episodes per seed and scenario.",
            "",
            "Use the relay-failure row as a stronger scenario-depth result. Keep scout failure as supporting trend evidence only.",
            "",
            "| Scenario | N | Success single/multi (%) | Success delta pp [95% CI] | Recovery single/multi (%) | Recovery delta pp [95% CI] | Recovery steps single/multi | Recovery-step delta [95% CI] | Status |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {SCENARIO_LABELS.get(row['scenario'], row['scenario'])} | {row['n_paired_episodes']} | "
            f"{fmt_pct(f(row, 'single_success_mean'))} / {fmt_pct(f(row, 'multi_success_mean'))} | "
            f"{fmt_delta_ci(f(row, 'delta_success_mean'), f(row, 'delta_success_ci_low'), f(row, 'delta_success_ci_high'), scale=100.0)} | "
            f"{fmt_pct(f(row, 'single_post_failure_chain_recovered_mean'))} / {fmt_pct(f(row, 'multi_post_failure_chain_recovered_mean'))} | "
            f"{fmt_delta_ci(f(row, 'delta_post_failure_chain_recovered_mean'), f(row, 'delta_post_failure_chain_recovered_ci_low'), f(row, 'delta_post_failure_chain_recovered_ci_high'), scale=100.0)} | "
            f"{fmt_steps(f(row, 'single_post_failure_chain_recovery_steps_mean'))} / {fmt_steps(f(row, 'multi_post_failure_chain_recovery_steps_mean'))} | "
            f"{fmt_delta_ci(f(row, 'delta_post_failure_chain_recovery_steps_mean'), f(row, 'delta_post_failure_chain_recovery_steps_ci_low'), f(row, 'delta_post_failure_chain_recovery_steps_ci_high'))} | "
            f"{strict_sensing_status(row)} |"
        )


def write_md(
    path: Path,
    rows: list[dict[str, str]],
    task_support_ablation: Path,
    role_pair_gate_ablation: Path,
    strict_sensing_recovery: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "Scenario",
        "Role",
        "N",
        "Success single/multi (%)",
        "Success delta pp [95% CI]",
        "Recovery single/multi (%)",
        "Recovery delta pp [95% CI]",
        "Recovery steps single/multi",
        "Recovery steps delta [95% CI]",
        "Episode steps delta [95% CI]",
        "Status",
    ]
    lines = [
        "# 3DOF Paper-Facing Main Table",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This table is an evidence triage table for manuscript drafting. It should not be treated as the final paper table until the remaining baselines and ablations are complete.",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["label"],
                    row["evidence_role"],
                    row["paired_episodes"],
                    f"{row['single_success_percent']} / {row['multi_success_percent']}",
                    row["success_delta_pp_ci95"],
                    f"{row['single_recovery_percent']} / {row['multi_recovery_percent']}",
                    row["recovery_delta_pp_ci95"],
                    f"{row['single_recovery_steps']} / {row['multi_recovery_steps']}",
                    row["recovery_steps_delta_ci95"],
                    row["steps_delta_ci95"],
                    row["claim_status"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Use In Paper",
            "",
            "- Main defensible claim: relay-failure recovery, where the multi-relation role graph improves post-failure kill-chain recovery probability and reduces recovery time.",
            "- Supporting claim: scout-failure and other communication/sensing perturbations show positive trends but need larger budgets or stronger baselines before being written as primary conclusions.",
            "- Boundary claim: communication range 0.75 is a stress case and should be reported honestly as mixed rather than forced into a positive result.",
        ]
    )
    append_task_support_ablation(lines, task_support_ablation)
    append_role_pair_gate_ablation(lines, role_pair_gate_ablation)
    append_strict_sensing_recovery(lines, strict_sensing_recovery)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def tex_escape(value: str) -> str:
    return value.replace("_", "\\_").replace("%", "\\%").replace("&", "\\&")


def write_tex(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% Auto-generated by scripts/build_3d_paper_tables.py",
        "\\begin{tabular}{llrrrrl}",
        "\\toprule",
        "Scenario & Role & $N$ & Success $\\Delta$ & Recovery $\\Delta$ & Recovery-step $\\Delta$ & Status \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{tex_escape(row['label'])} & {tex_escape(row['evidence_role'])} & {row['paired_episodes']} & "
            f"{tex_escape(row['success_delta_pp_ci95'])} & {tex_escape(row['recovery_delta_pp_ci95'])} & "
            f"{tex_escape(row['recovery_steps_delta_ci95'])} & {tex_escape(row['claim_status'])} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    formal_rows = read_csv(args.formal_summary)
    recovery_rows = read_csv(args.recovery_summary)
    rows = build_rows(formal_rows, recovery_rows)
    write_csv(args.out_csv, rows)
    write_md(args.out_md, rows, args.task_support_ablation, args.role_pair_gate_ablation, args.strict_sensing_recovery)
    write_tex(args.out_tex, rows)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.out_tex}")


if __name__ == "__main__":
    main()
