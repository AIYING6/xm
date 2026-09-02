"""Write a read-only long-horizon value audit for historical DRTP candidates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("configs/historical_long_horizon_value_audit_20260902.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/historical_long_horizon_value_audit_20260902"))
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    contract = f"""# Long-horizon value audit contract

Protocol: `{registry['protocol']}`

## Authorized work

This is a read-only artifact audit. It inspects historical training lengths, checkpoint availability, completed matched performance outcomes, and training-curve maturity evidence. It does **not** assert that a training objective curve is a task-performance curve.

## Prohibitions

{', '.join(registry['prohibitions'])}.

## Decision standard

`LONG_HORIZON_RETEST_JUSTIFIED` requires: a local matched performance signal, clearly sub-mature historical budget, no evidence of mature negative replication, observable evidence that the relative ranking might change with horizon, exact frozen semantic recovery, and no parameter adjustment. `WEAKLY_JUSTIFIED` means local upside survives but the direct long-horizon rationale is missing. `NOT_JUSTIFIED` means a longer comparable failure exists or the record supplies no evidence that time, rather than cohort dependence, caused the result.
"""
    (output / "LONG_HORIZON_VALUE_AUDIT_CONTRACT.md").write_text(contract, encoding="utf-8")

    for candidate in registry["candidates"]:
        short = candidate["method"].split()[0].replace("-DRTP", "").replace("-", "_").upper()
        lines = [f"# {candidate['method']} long-horizon audit", ""]
        lines += [
            f"**Verdict:** `{candidate['verdict']}`.", "",
            f"Historical budgets: {candidate['historical_budgets_million']}M env steps.",
            f"Saved task-policy/runtime milestones: {candidate['historical_checkpoints_million']}M.",
            f"Exact runtime recovery recorded: `{candidate['runtime_resumable']}`.",
            "",
            "## Existing matched performance evidence",
            "",
            f"Development: mean {candidate['development_effect']['mean']:+.3f}; median {candidate['development_effect']['median']:+.3f}; wins {candidate['development_effect']['wins']} versus Original DRTP.",
        ]
        for key, value in candidate.items():
            if key.startswith("replication") or key == "closest_longer_replication" or key == "independent_replication":
                lines.append(
                    f"{key.replace('_', ' ').title()}: {value['budget_million']}M, mean {value['mean']:+.3f}, "
                    f"median {value['median']:+.3f}, wins {value['wins']}, new catastrophes {value['new_catastrophic']}."
                )
        lines += ["", "## Curve maturity", "", candidate["training_curve_status"], "", "## Audit conclusion", "", candidate["reason"]]
        filename = {"S2": "S2_LONG_HORIZON_AUDIT.md", "KLR": "KLR_LONG_HORIZON_AUDIT.md", "PP": "PP_LONG_HORIZON_AUDIT.md"}[short]
        (output / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")

    rows = [
        "method,historical_budgets_million,checkpoints_million,runtime_resumable,curve_maturity_evidence,long_horizon_verdict",
    ]
    for candidate in registry["candidates"]:
        budgets = ";".join(map(str, candidate["historical_budgets_million"]))
        checks = ";".join(map(str, candidate["historical_checkpoints_million"]))
        curve = candidate["training_curve_status"].replace(",", ";")
        rows.append(f"{candidate['method']},{budgets},{checks},{candidate['runtime_resumable']},\"{curve}\",{candidate['verdict']}")
    (output / "HISTORICAL_CURVE_MATURITY_MATRIX.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    ranking = """# Long-horizon candidate ranking

## Ranking

1. **KLR — `LONG_HORIZON_RETEST_WEAKLY_JUSTIFIED`.** It retains one positive 0.5M replication cohort, has exact runtime states, and has not been tested at 1M. This is a relative rank, not evidence sufficient for a long-horizon experiment.
2. **S2 Conservative-DRTP — `LONG_HORIZON_RETEST_NOT_JUSTIFIED`.** It is operationally simple and locally clean, but the closest 1M conservative replication reversed the local result.
3. **PP-DRTP — `LONG_HORIZON_RETEST_NOT_JUSTIFIED`.** Its P3 upside was substantial, but P4 reversed with additional probe cost and two new catastrophes.

## Contract decision

`RANK1_LONG_HORIZON_FROZEN_CONTRACT`: **NOT WARRANTED**.

The record has no completed intermediate task-evaluation trajectory that supports the required claim that additional horizon is likely to reverse the KLR ranking. The observed split is at least as consistent with cohort dependence as with under-training. Generating a contract now would be a new long-horizon bet, not a continuation justified by historical evidence.
"""
    (output / "LONG_HORIZON_CANDIDATE_RANKING.md").write_text(ranking, encoding="utf-8")

    paper = """# Paper value if performance, rather than stability, is the target

A method can have paper value as **performance-enhanced but reliability-limited** if, at a mature predeclared horizon, it demonstrates positive paired mean and median effects, a majority of positive training seeds, fault/OOD improvement, nominal retention, and transparent safety and cohort reporting. Lower-tail and dispersion outcomes must still be reported, but need not improve to support a bounded performance claim.

The present record does not meet that standard for a replacement candidate. Local S2, KLR, and PP signals are useful historical evidence, but they are not mature, cross-cohort performance confirmation. For the current A-line paper, Original DRTP remains the sole method with formal long-horizon positive evidence; reliability boundaries should be disclosed without allowing unreplicated patches to displace the main contribution.
"""
    (output / "PAPER_VALUE_IF_PERFORMANCE_ONLY.md").write_text(paper, encoding="utf-8")

    result = {
        "protocol": registry["protocol"],
        "mode": registry["mode"],
        "training_started": False,
        "evaluation_started": False,
        "a_line_modified": False,
        "candidate_verdicts": {item["method"]: item["verdict"] for item in registry["candidates"]},
        "ranking": registry["ranking"],
        "rank1_long_horizon_frozen_contract_warranted": registry["rank1_contract_warranted"],
        "automatic_continuation_authorized": False,
    }
    (output / "LONG_HORIZON_VALUE_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "LONG_HORIZON_VALUE_AUDIT_COMPLETE", **result}, indent=2))


if __name__ == "__main__":
    main()
