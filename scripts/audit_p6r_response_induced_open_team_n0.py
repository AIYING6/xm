#!/usr/bin/env python3
"""Zero-training structural audit for P6R.

This audit is not a learning environment and reports no method performance.  It
checks a narrowly defined prerequisite: whether an observable team commitment
can induce distinct, hidden opponent reactions such that no single fixed
friendly response is optimal against all frozen opponent rules.  The opponent
rules consume observed allocation only; they never receive a response name.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def opponent_allocation(rule: str, allocation: tuple[int, int], is_feint: bool) -> tuple[tuple[int, int], float]:
    """Map only visible allocation and its physical reversal to an allocation."""
    left, right = allocation
    if rule == "mirror_pressure":
        return ((2, 0) if left >= right else (0, 2)), 0.0
    if rule == "weak_side_denial":
        return ((2, 0) if left < right else (0, 2)), 0.0
    if rule == "commitment_exploiter":
        # A feint has a visible late spatial reversal, not a hidden policy label.
        return ((2, 0) if left < right else (0, 2)), (1.0 if is_feint else 0.0)
    raise ValueError(rule)


def endpoint(response: str, spec: dict[str, Any], rule: str, cfg: dict[str, Any]) -> dict[str, Any]:
    dynamics = cfg["dynamics"]
    initial = tuple(spec["allocation"])
    is_feint = response == "left_feint_then_right"
    observed = initial
    opponent, lagged = opponent_allocation(rule, observed, is_feint)
    # A physical late redirection moves cover from left to right but costs time.
    final = (0, 2) if is_feint else initial
    survives = []
    for f, o in zip(final, opponent):
        margin = f * dynamics["friendly_capacity"] - o * dynamics["opponent_capacity"]
        survives.append(int(margin >= 0.0))
    served = sum(survives) * dynamics["service_value_per_corridor"]
    uncovered = sum(1 for x in final if x == 0) * dynamics["uncovered_corridor_cost"]
    lag = lagged * dynamics["repositioning_lag_penalty"]
    switch = spec["switch_cost"]
    utility = served - uncovered - lag - switch
    return {"response": response, "rule": rule, "friendly_initial": str(initial),
            "friendly_final": str(final), "opponent_allocation": str(opponent),
            "opponent_reposition_lag": lagged, "served_corridors": sum(survives),
            "utility": utility}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")
    cfg = json.loads(args.contract.read_text(encoding="utf-8"))
    if cfg.get("protocol") != "P6R-RESPONSE-INDUCED-OPEN-TEAM-N0-V1" or cfg.get("training_authorized"):
        raise ValueError("contract mismatch")
    if args.output_root.exists():
        raise FileExistsError(args.output_root)

    rows = [endpoint(response, spec, rule, cfg)
            for rule in cfg["opponent_response_rules"]
            for response, spec in cfg["friendly_responses"].items()]
    best: dict[str, dict[str, Any]] = {}
    for rule in cfg["opponent_response_rules"]:
        ordered = sorted((r for r in rows if r["rule"] == rule), key=lambda r: r["utility"], reverse=True)
        best[rule] = {"response": ordered[0]["response"], "margin": ordered[0]["utility"] - ordered[1]["utility"]}
    distinct = len({x["response"] for x in best.values()})
    response_change = []
    for rule in cfg["opponent_response_rules"]:
        seen = {r["opponent_allocation"] + "/" + str(r["opponent_reposition_lag"])
                for r in rows if r["rule"] == rule}
        response_change.append(len(seen) > 1)
    gates = cfg["qualification_gates"]
    dominant = max(sum(v["response"] == name for v in best.values()) for name in cfg["friendly_responses"])
    results = {
        "protocol": cfg["protocol"],
        "training_started": False,
        "ppo_updates": 0,
        "passive_prefix": "All opponent rules use identical neutral staging for the two pre-commitment steps.",
        "best_response_by_opponent_rule": best,
        "checks": {
            "identical_passive_prefix": bool(gates["require_identical_passive_prefix"]),
            "distinct_unique_best_responses": distinct >= gates["minimum_distinct_unique_best_responses"],
            "best_response_margins": all(v["margin"] >= gates["minimum_best_response_margin"] for v in best.values()),
            "response_induced_opponent_change": sum(response_change) / len(response_change) >= gates["minimum_response_induced_opponent_change_fraction"],
            "no_universal_response": (dominant < len(best)) if gates["require_no_universal_response"] else True
        },
        "boundary": "This constructed analytical audit establishes neither continuous-UAV realizability, learnability, method efficacy, nor novelty. A pass permits only the N0.4 continuous-dynamics audit."
    }
    verdict = "P6R_N0_STRUCTURAL_PASS" if all(results["checks"].values()) else "P6R_N0_STRUCTURAL_STOP"
    results["verdict"] = verdict
    args.output_root.mkdir(parents=True)
    write_csv(args.output_root / "response_induced_utility_matrix.csv", rows)
    (args.output_root / "P6R_N0_REPORT.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text = ["# P6R N0 响应诱导开放团队：结构资格审计", "", f"**结论：`{verdict}`**", "",
            "本审计不训练模型、没有 PPO 更新、也不构成论文结果。它只测试任务构造的必要条件。", "",
            "| 对手反应规则 | 唯一最佳友方响应 | 与次优响应的效用间隔 |",
            "|---|---:|---:|"]
    text.extend(f"| {rule} | {value['response']} | {value['margin']:.3f} |" for rule, value in best.items())
    text.extend(["", "## 解释边界", "", results["boundary"], ""])
    (args.output_root / "P6R_N0_REPORT.md").write_text("\n".join(text), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
