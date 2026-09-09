#!/usr/bin/env python3
"""Read-only foundation audit for the frozen P6 CIRU topic.

The script performs deterministic heuristic cross-play only.  It never creates
or updates a policy checkpoint and does not authorize learning experiments.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np


POLICY_NAMES = ("R1", "R2", "R3", "R4")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _mean_pairwise_distance(states: np.ndarray, alive: np.ndarray, scale: float) -> float:
    ids = np.flatnonzero(alive)
    if len(ids) < 2:
        return 0.0
    values = [np.linalg.norm(states[i, :3] - states[j, :3]) / scale for i, j in combinations(ids, 2)]
    return float(np.mean(values))


def behavior_snapshot(env: Any) -> np.ndarray:
    """Return translation-tolerant, dimensionless red-team behavior features."""
    b_ids = np.flatnonzero(env.blue_alive)
    r_ids = np.flatnonzero(env.red_alive)
    bf = env.cfg.battlefield
    diag = math.sqrt((bf.x_max - bf.x_min) ** 2 + (bf.y_max - bf.y_min) ** 2 + (bf.z_max - bf.z_min) ** 2)
    speed_scale = env.cfg.dynamics.v_max
    if len(b_ids) and len(r_ids):
        bc = np.mean(env.blue_states[b_ids, :3], axis=0)
        rc = np.mean(env.red_states[r_ids, :3], axis=0)
        delta = (rc - bc) / diag
        nearest = min(np.linalg.norm(env.red_states[i, :3] - env.blue_states[j, :3]) for i in r_ids for j in b_ids) / diag
        nearest_targets = []
        for i in r_ids:
            nearest_targets.append(int(b_ids[np.argmin(np.linalg.norm(env.blue_states[b_ids, :3] - env.red_states[i, :3], axis=1))]))
        concentration = max(nearest_targets.count(j) for j in set(nearest_targets)) / len(nearest_targets)
    else:
        delta = np.zeros(3)
        nearest = 1.0
        concentration = 0.0
    if len(r_ids):
        psi = env.red_states[r_ids, 4]
        coherence = math.hypot(float(np.mean(np.sin(psi))), float(np.mean(np.cos(psi))))
        mean_speed = float(np.mean(env.red_states[r_ids, 3])) / speed_scale
    else:
        coherence = mean_speed = 0.0
    return np.asarray([
        *delta,
        nearest,
        _mean_pairwise_distance(env.red_states, env.red_alive, diag),
        coherence,
        mean_speed,
        concentration,
        float(np.mean(env.red_alive)),
    ], dtype=np.float64)


def summarize_trace(trace: list[np.ndarray], prefix_steps: int) -> np.ndarray:
    if not trace:
        return np.zeros(27, dtype=np.float64)
    arr = np.stack(trace[:prefix_steps])
    first = arr[0]
    last = arr[-1]
    mean = np.mean(arr, axis=0)
    return np.concatenate([mean, last, last - first])


def _distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a - b))))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--osta-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source-archive", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract.get("protocol") != "P6-CIRU-Z1-Z2-READONLY-AUDIT-V1" or not contract.get("read_only"):
        raise ValueError("contract mismatch")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    if args.source_archive and _sha256(args.source_archive) != contract["source_archive_sha256"]:
        raise ValueError("OSTA source archive SHA256 mismatch")

    root = args.osta_root.resolve()
    sys.path.insert(0, str(root))
    from envs.uav_game import MultiUAVCombatEnv
    from evaluation.scenarios import load_scenarios, paired_opponent_seed
    from opponents.controllers.config import load_tactical_controller_config
    from opponents.heuristic import R1NearestPolicy, R2FocusFirePolicy, R3AssignmentPolicy, R4FlankingPolicy, TeamContext
    from utils.config import load_env_config

    policy_classes = dict(zip(POLICY_NAMES, (R1NearestPolicy, R2FocusFirePolicy, R3AssignmentPolicy, R4FlankingPolicy)))
    env_cfg = load_env_config(root / "configs/env_3v3_v2.yaml")
    ctrl = load_tactical_controller_config(root / "configs/opponents/controller_v1.yaml")
    scenarios = load_scenarios(root / contract["scenario_tape"], env_cfg)[: int(contract["scenario_count"])]
    if len(scenarios) != int(contract["scenario_count"]):
        raise ValueError("scenario tape shorter than frozen contract")

    records: list[dict[str, Any]] = []
    vectors: dict[tuple[str, str, int], np.ndarray] = {}
    for red_name in contract["red_strategies"]:
        for blue_name in contract["blue_responses"]:
            for scenario in scenarios:
                env = MultiUAVCombatEnv(env_cfg)
                blue = policy_classes[blue_name](env_cfg.dynamics, ctrl)
                red = policy_classes[red_name](env_cfg.dynamics, ctrl)
                env.reset(options={"scenario": scenario})
                seed = paired_opponent_seed(int(contract["base_policy_seed"]), scenario.scenario_id)
                blue.reset(seed + 100_000 * (POLICY_NAMES.index(blue_name) + 1))
                red.reset(seed + 1_000 * (POLICY_NAMES.index(red_name) + 1))
                trace: list[np.ndarray] = []
                total_return = 0.0
                while True:
                    trace.append(behavior_snapshot(env))
                    bctx = TeamContext(env.blue_states.copy(), env.blue_alive.copy(), env.red_states.copy(), env.red_alive.copy(), env.step_count)
                    rctx = TeamContext(env.red_states.copy(), env.red_alive.copy(), env.blue_states.copy(), env.blue_alive.copy(), env.step_count)
                    _, rewards, terminated, truncated, info = env.step(blue.act(bctx), red.act(rctx))
                    total_return += float(rewards["blue"])
                    if terminated or truncated:
                        break
                vector = summarize_trace(trace, int(contract["prefix_steps"]))
                vectors[(red_name, blue_name, scenario.scenario_id)] = vector
                records.append({
                    "red_strategy": red_name, "blue_response": blue_name,
                    "scenario_id": scenario.scenario_id, "steps": env.step_count,
                    "blue_return": total_return, "blue_clean_win": int(info.get("clean_winner") == "blue"),
                    "timeout": int(truncated), "blue_alive_end": int(env.blue_alive.sum()),
                    "red_alive_end": int(env.red_alive.sum()),
                })

    z1_rows: list[dict[str, Any]] = []
    case_maxima = []
    for red_name in contract["red_strategies"]:
        for scenario in scenarios:
            distances = []
            for a, b in combinations(contract["blue_responses"], 2):
                d = _distance(vectors[(red_name, a, scenario.scenario_id)], vectors[(red_name, b, scenario.scenario_id)])
                distances.append(d)
                z1_rows.append({"red_strategy": red_name, "scenario_id": scenario.scenario_id,
                                "blue_response_a": a, "blue_response_b": b, "behavior_distance": d})
            case_maxima.append(max(distances))

    means: dict[tuple[str, str], float] = {}
    for red_name in contract["red_strategies"]:
        for blue_name in contract["blue_responses"]:
            vals = [r["blue_return"] for r in records if r["red_strategy"] == red_name and r["blue_response"] == blue_name]
            means[(red_name, blue_name)] = float(np.mean(vals))
    best: dict[str, tuple[str, float]] = {}
    for red_name in contract["red_strategies"]:
        ordered = sorted(((means[(red_name, b)], b) for b in contract["blue_responses"]), reverse=True)
        best[red_name] = (ordered[0][1], ordered[0][0] - ordered[1][0])

    ref = contract["reference_blue_response_for_aliasing"]
    z2_rows: list[dict[str, Any]] = []
    qualifying = 0
    gates = contract["gates"]
    for a, b in combinations(contract["red_strategies"], 2):
        va = np.mean([vectors[(a, ref, s.scenario_id)] for s in scenarios], axis=0)
        vb = np.mean([vectors[(b, ref, s.scenario_id)] for s in scenarios], axis=0)
        dist = _distance(va, vb)
        disagrees = best[a][0] != best[b][0]
        margins_ok = min(best[a][1], best[b][1]) >= gates["z2_min_best_response_margin"]
        qualifies = dist <= gates["z2_alias_distance_threshold"] and disagrees and margins_ok
        qualifying += int(qualifies)
        z2_rows.append({"red_a": a, "red_b": b, "prefix_behavior_distance": dist,
                        "best_response_a": best[a][0], "margin_a": best[a][1],
                        "best_response_b": best[b][0], "margin_b": best[b][1],
                        "rank_disagreement": int(disagrees), "qualifies": int(qualifies)})

    shifted_fraction = float(np.mean(np.asarray(case_maxima) > gates["z1_case_shift_threshold"]))
    median_shift = float(np.median(case_maxima))
    z1_pass = shifted_fraction >= gates["z1_min_shifted_case_fraction"] and median_shift >= gates["z1_min_median_max_shift"]
    z2_pass = qualifying >= gates["z2_min_qualifying_pairs"]
    verdict = "CIRU_STAGE0_Z1_Z2_PASS" if z1_pass and z2_pass else "CIRU_STAGE0_FOUNDATION_STOP"
    report = {
        "protocol": contract["protocol"], "verdict": verdict,
        "read_only": True, "training_started": False, "ppo_updates": 0,
        "scenario_count": len(scenarios), "rollout_count": len(records),
        "z1": {"pass": z1_pass, "shifted_case_fraction": shifted_fraction,
               "median_case_max_behavior_distance": median_shift,
               "case_count": len(case_maxima)},
        "z2": {"pass": z2_pass, "qualifying_pair_count": qualifying,
               "pair_count": len(z2_rows), "best_response_by_red": {k: {"response": v[0], "margin": v[1]} for k, v in best.items()}},
        "interpretation_boundary": "Z1 establishes response-conditioned trajectory variation in scripted cross-play. Z2 is an existence test in the frozen heuristic set; neither result demonstrates learned CIRU performance or causal generalization.",
    }
    args.output_root.mkdir(parents=True)
    _write_csv(args.output_root / "crossplay_endpoints.csv", records)
    _write_csv(args.output_root / "z1_response_induced_shift.csv", z1_rows)
    _write_csv(args.output_root / "z2_alias_rank_pairs.csv", z2_rows)
    (args.output_root / "P6_CIRU_Z1_Z2_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = ["# P6 CIRU Z1–Z2 零训练审计", "", f"**结论：`{verdict}`**", "",
          f"- Z1 响应诱导偏移：{'PASS' if z1_pass else 'FAIL'}；变化案例比例 {shifted_fraction:.3f}，案例最大距离中位数 {median_shift:.4f}。",
          f"- Z2 行为混叠且最佳响应分歧：{'PASS' if z2_pass else 'FAIL'}；合格对手对 {qualifying}/{len(z2_rows)}。", "",
          "该审计只使用冻结脚本策略进行确定性交叉 rollout，不训练模型、不更新参数。Z1/Z2 通过仅允许继续检查响应专门化与 oracle headroom，不能证明 CIRU 有效。", ""]
    (args.output_root / "P6_CIRU_Z1_Z2_REPORT.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
