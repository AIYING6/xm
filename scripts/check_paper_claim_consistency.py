from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_rows(rel: str) -> list[dict]:
    with (ROOT / rel).open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def row_by(rows: list[dict], **criteria: object) -> dict:
    matches = []
    for row in rows:
        ok = True
        for key, value in criteria.items():
            if isinstance(value, float):
                ok = abs(float(row[key]) - value) < 1e-6
            else:
                ok = row[key] == str(value)
            if not ok:
                break
        if ok:
            matches.append(row)
    if len(matches) != 1:
        raise AssertionError(f"expected one row for {criteria}, got {len(matches)}")
    return matches[0]


def f(row: dict, key: str) -> float:
    return float(row[key])


def rounded(value: float) -> str:
    return f"{value:.3f}"


def check_final_main_claims() -> list[str]:
    rows = read_rows("results/final_comm_300_summary.csv")
    errors = []
    radii = [4.0, 6.0, 8.0, 10.0]
    for radius in radii:
        ea = row_by(rows, method="EA-RG-MAPPO-S", radius=radius)
        mappo = row_by(rows, method="MAPPO", radius=radius)
        gat = row_by(rows, method="GAT-MAPPO", radius=radius)
        if f(ea, "collision_mean") > 0.10:
            errors.append(f"EA collision above paper threshold at radius={radius}: {ea['collision_mean']}")
        if f(ea, "collision_mean") >= f(mappo, "collision_mean"):
            errors.append(f"EA collision not lower than MAPPO at radius={radius}")
        if f(ea, "collision_mean") >= f(gat, "collision_mean"):
            errors.append(f"EA collision not lower than GAT-MAPPO at radius={radius}")
        if f(ea, "success_mean") < 0.87:
            errors.append(f"EA success too low for main claim at radius={radius}: {ea['success_mean']}")
    return errors


def check_speed_robustness_claims() -> list[str]:
    rows = read_rows("results/speed_robustness_summary.csv")
    errors = []
    for radius in [4.0, 8.0]:
        speed = 0.9
        ea = row_by(rows, method="EA-RG-MAPPO-S", radius=radius, target_speed=speed)
        mappo = row_by(rows, method="MAPPO", radius=radius, target_speed=speed)
        gat = row_by(rows, method="GAT-MAPPO", radius=radius, target_speed=speed)
        if f(ea, "collision_mean") >= f(mappo, "collision_mean"):
            errors.append(f"speed robustness: EA collision not lower than MAPPO at radius={radius}, speed={speed}")
        if f(ea, "collision_mean") >= f(gat, "collision_mean"):
            errors.append(f"speed robustness: EA collision not lower than GAT-MAPPO at radius={radius}, speed={speed}")
        if f(ea, "success_mean") < f(gat, "success_mean") and radius == 8.0:
            # Radius 8 is the harder speed appendix case where EA should still
            # keep higher success than GAT at the highest tested speed.
            errors.append("speed robustness: EA success below GAT-MAPPO at radius=8, speed=0.90")
    return errors


def check_edge_masking_claims() -> list[str]:
    rows = read_rows("results/edge_feature_ablation_summary.csv")
    errors = []
    for radius in [4.0, 8.0]:
        base = row_by(rows, radius=radius, ablation="none")
        comm = row_by(rows, radius=radius, ablation="zero_comm_target_flags")
        if f(comm, "success_mean") >= f(base, "success_mean"):
            errors.append(f"edge masking: comm/target masking did not reduce success at radius={radius}")
        if f(comm, "collision_mean") <= f(base, "collision_mean"):
            errors.append(f"edge masking: comm/target masking did not increase collision at radius={radius}")

    # Do not overclaim: full edge masking should not be treated as a
    # catastrophic degradation, because local obs and adjacency retain
    # redundant information.
    for radius in [4.0, 8.0]:
        base = row_by(rows, radius=radius, ablation="none")
        all_edge = row_by(rows, radius=radius, ablation="zero_all_edge_features")
        if abs(f(all_edge, "success_mean") - f(base, "success_mean")) > 0.05:
            errors.append(f"edge masking: all-edge success delta too large for weak-sensitivity claim at radius={radius}")
    return errors


def check_paired_ci_claims() -> list[str]:
    rows = read_rows("results/final_300_paired_statistics.csv")
    errors = []
    if len(rows) != 16:
        errors.append(f"paired CI rows expected=16 actual={len(rows)}")
        return errors
    for row in rows:
        if f(row, "mean_diff") <= 0:
            errors.append(
                f"paired CI mean is not positive: baseline={row['baseline']} "
                f"radius={row['radius']} metric={row['metric']}"
            )

    gat_r4_collision = row_by(
        rows,
        baseline="GAT-MAPPO",
        radius=4.0,
        metric="collision_reduction",
    )
    gat_r8_success = row_by(
        rows,
        baseline="GAT-MAPPO",
        radius=8.0,
        metric="success_gain",
    )
    gat_r8_collision = row_by(
        rows,
        baseline="GAT-MAPPO",
        radius=8.0,
        metric="collision_reduction",
    )
    for label, row in [
        ("GAT r4 collision reduction", gat_r4_collision),
        ("GAT r8 success gain", gat_r8_success),
        ("GAT r8 collision reduction", gat_r8_collision),
    ]:
        if f(row, "ci95_low") <= 0:
            errors.append(f"paired CI lower bound not positive for {label}: {row['ci95_low']}")
    return errors


def check_comm_dropout_claims() -> list[str]:
    rows = read_rows("results/comm_dropout_robustness_summary.csv")
    errors = []
    if len(rows) != 18:
        errors.append(f"communication-dropout summary rows expected=18 actual={len(rows)}")
        return errors
    for radius in [4.0, 8.0]:
        for dropout in [0.0, 0.25, 0.5]:
            ea = row_by(rows, method="EA-RG-MAPPO-S", radius=radius, comm_dropout_prob=dropout)
            mappo = row_by(rows, method="MAPPO", radius=radius, comm_dropout_prob=dropout)
            gat = row_by(rows, method="GAT-MAPPO", radius=radius, comm_dropout_prob=dropout)
            if f(ea, "collision_mean") >= f(mappo, "collision_mean"):
                errors.append(f"dropout diagnostic: EA collision not lower than MAPPO at radius={radius}, dropout={dropout}")
            if f(ea, "collision_mean") >= f(gat, "collision_mean"):
                errors.append(f"dropout diagnostic: EA collision not lower than GAT at radius={radius}, dropout={dropout}")
    return errors


def check_aggregate_robustness_claims() -> list[str]:
    rows = read_rows("results/aggregate_robustness_summary.csv")
    errors = []
    if len(rows) != 6:
        errors.append(f"aggregate robustness rows expected=6 actual={len(rows)}")
        return errors

    for scope in ["final_cross_radius", "dropout_diagnostic"]:
        ea = row_by(rows, scope=scope, method="EA-RG-MAPPO-S")
        mappo = row_by(rows, scope=scope, method="MAPPO")
        gat = row_by(rows, scope=scope, method="GAT-MAPPO")
        for baseline_name, baseline in [("MAPPO", mappo), ("GAT-MAPPO", gat)]:
            if f(ea, "mean_success") <= f(baseline, "mean_success"):
                errors.append(f"aggregate: EA mean_success not higher than {baseline_name} in {scope}")
            if f(ea, "mean_collision") >= f(baseline, "mean_collision"):
                errors.append(f"aggregate: EA mean_collision not lower than {baseline_name} in {scope}")
            if f(ea, "worst_collision") >= f(baseline, "worst_collision"):
                errors.append(f"aggregate: EA worst_collision not lower than {baseline_name} in {scope}")
            if f(ea, "conservative_margin") <= f(baseline, "conservative_margin"):
                errors.append(f"aggregate: EA conservative_margin not higher than {baseline_name} in {scope}")

    final_ea = row_by(rows, scope="final_cross_radius", method="EA-RG-MAPPO-S")
    dropout_ea = row_by(rows, scope="dropout_diagnostic", method="EA-RG-MAPPO-S")
    dropout_mappo = row_by(rows, scope="dropout_diagnostic", method="MAPPO")
    dropout_gat = row_by(rows, scope="dropout_diagnostic", method="GAT-MAPPO")
    required_numbers = [
        rounded(f(final_ea, "mean_success")),
        rounded(f(final_ea, "mean_collision")),
        rounded(f(final_ea, "conservative_margin")),
        rounded(f(dropout_ea, "mean_success")),
        rounded(f(dropout_ea, "mean_collision")),
        rounded(f(dropout_ea, "conservative_margin")),
        rounded(f(dropout_ea, "worst_collision")),
        rounded(f(dropout_mappo, "worst_collision")),
        rounded(f(dropout_gat, "worst_collision")),
    ]
    text_files = [
        "results/latex_aggregate_robustness_table.tex",
        "results/aggregate_robustness_summary.md",
        "docs/evidence_chain_status.md",
        "paper_latex/sections/08_appendix_experiments.tex",
        "paper_latex_en/sections/08_appendix_experiments.tex",
    ]
    for rel in text_files:
        text = (ROOT / rel).read_text(encoding="utf-8")
        missing = [value for value in required_numbers if value not in text]
        if missing:
            errors.append(f"aggregate: {rel} missing rounded values {missing}")
    return errors


def check_radius_interpolation_claims() -> list[str]:
    rows = read_rows("results/radius_interpolation_summary.csv")
    errors = []
    if len(rows) != 9:
        errors.append(f"radius interpolation rows expected=9 actual={len(rows)}")
        return errors
    for radius in [5.0, 7.0, 9.0]:
        ea = row_by(rows, method="EA-RG-MAPPO-S", radius=radius)
        mappo = row_by(rows, method="MAPPO", radius=radius)
        gat = row_by(rows, method="GAT-MAPPO", radius=radius)
        if f(ea, "collision_mean") >= f(mappo, "collision_mean"):
            errors.append(f"radius interpolation: EA collision not lower than MAPPO at radius={radius}")
        if f(ea, "collision_mean") >= f(gat, "collision_mean"):
            errors.append(f"radius interpolation: EA collision not lower than GAT at radius={radius}")
        if f(ea, "success_mean") < 0.86:
            errors.append(f"radius interpolation: EA success below appendix threshold at radius={radius}")

    required_numbers = ["0.067", "0.100", "0.227", "0.200", "0.153", "0.113", "0.140", "0.173"]
    text_files = [
        "results/latex_radius_interpolation_table.tex",
        "results/radius_interpolation_notes.md",
        "paper_latex/sections/08_appendix_experiments.tex",
        "paper_latex_en/sections/08_appendix_experiments.tex",
    ]
    for rel in text_files:
        text = (ROOT / rel).read_text(encoding="utf-8")
        missing = [value for value in required_numbers if value not in text]
        if missing:
            errors.append(f"radius interpolation: {rel} missing values {missing}")
    return errors


def main() -> None:
    errors = []
    errors.extend(check_final_main_claims())
    errors.extend(check_speed_robustness_claims())
    errors.extend(check_edge_masking_claims())
    errors.extend(check_paired_ci_claims())
    errors.extend(check_comm_dropout_claims())
    errors.extend(check_aggregate_robustness_claims())
    errors.extend(check_radius_interpolation_claims())

    print("claim groups checked: final_main, speed_robustness, edge_masking, paired_ci, comm_dropout, aggregate_robustness, radius_interpolation")
    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
