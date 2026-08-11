"""Checkpoint-only mission-stage localization for frozen L4 policies."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR
from scripts import run_l4_corrected_contract_requalification as l4r
from scripts import run_new_project_l0_single_interceptor as l0

OUT = ROOT / "results" / "l4_mission_failure_stage_localization"
CHECKPOINT_ROOT = ROOT / "results" / "l4_corrected_contract_requalification"
TRAIN_SEEDS = (8901, 8902)
EPISODE_SEEDS = tuple(range(890_000, 890_032))
PROTOCOL = "L4_MISSION_FAILURE_STAGE_LOCALIZATION_V1"


def localize(cfg, episode_seed: int, agent) -> dict[str, object]:
    env = l0.make_env(cfg, episode_seed, training=False)
    obs, share, graph = env.reset()
    attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR})
    typ = env.config.blue_types[attacker]
    evidence = approach = geometry = aligned_commit = hold4 = False
    min_range = float("inf"); max_dwell = dwell = max_hold = 0
    while True:
        action = np.asarray(l0.agent_actions(agent, obs, share, graph), dtype=np.float32).reshape(env.num_agents, 3)
        for i, role in enumerate(env.config.blue_types):
            if role.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}: action[i, 2] = -1.0
        obs, share, graph, _reward, dones, info = env.step(action)
        evidence = evidence or bool(env._has_fresh_target_cache(attacker))
        distance = float(np.linalg.norm(env.red_pos[0] - env.blue_pos[attacker])); min_range = min(min_range, distance)
        approach = approach or distance <= typ.attack_range_max
        valid = bool(env._in_true_standoff_envelope(attacker, typ)); geometry = geometry or valid
        dwell = dwell + 1 if valid else 0; max_dwell = max(max_dwell, dwell)
        aligned_commit = aligned_commit or bool(valid and env.last_engage_commit[attacker] > 0.5)
        max_hold = max(max_hold, int(env.engage_commit_hold)); hold4 = hold4 or max_hold >= env.config.engage_commit_hold_steps
        if bool(np.all(dones)):
            outcome = l0.outcome(info)
            if outcome == "NEUTRALIZED": stage = "NEUTRALIZED"
            elif not evidence: stage = "NO_LEGAL_TARGET_EVIDENCE"
            elif not approach: stage = "NO_ATTACK_RANGE_ACQUISITION"
            elif not geometry: stage = "NO_LEGAL_GEOMETRY"
            elif not aligned_commit: stage = "NO_COMMIT_IN_GEOMETRY"
            elif not hold4: stage = "NO_FOUR_STEP_HOLD"
            else: stage = "POST_HOLD_NON_NEUTRAL_TERMINATION"
            return {"episode_seed": episode_seed, "terminal_outcome": outcome, "failure_stage": stage, "terminal_step": int(info["step"]), "legal_target_evidence": int(evidence), "attack_range_acquired": int(approach), "legal_geometry_acquired": int(geometry), "commit_in_geometry": int(aligned_commit), "four_step_hold": int(hold4), "min_attacker_target_range": min_range, "max_geometry_dwell": max_dwell, "max_commit_hold": max_hold}


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()): raise FileExistsError(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True, exist_ok=True); rows = []; hashes = {}
    for train_seed in TRAIN_SEEDS:
        checkpoint = CHECKPOINT_ROOT / f"l4_corrected_contract_seed{train_seed}" / "actor_critic_latest.pt"
        if not checkpoint.exists(): raise FileNotFoundError(checkpoint)
        hashes[str(train_seed)] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        cfg = l4r.cfg(train_seed, OUT / "template", updates=1)
        agent = l0.load_agent(cfg, checkpoint)
        rows.extend({"training_seed": train_seed, **localize(cfg, episode_seed, agent)} for episode_seed in EPISODE_SEEDS)
    with (OUT / "stage_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summaries = []; dominant = []
    for train_seed in TRAIN_SEEDS:
        failed = [r for r in rows if r["training_seed"] == train_seed and r["failure_stage"] != "NEUTRALIZED"]
        counts = {stage: sum(r["failure_stage"] == stage for r in failed) for stage in sorted({r["failure_stage"] for r in failed})}
        top = max(counts, key=counts.get) if counts else "NONE"
        rate = counts.get(top, 0) / len(failed) if failed else 0.0
        dominant.append((top, rate)); summaries.extend({"training_seed": train_seed, "failure_stage": stage, "episodes": len(failed), "count": count, "failure_fraction": count / len(failed) if failed else 0.0} for stage, count in counts.items())
    with (OUT / "stage_summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0])); writer.writeheader(); writer.writerows(summaries)
    stable = dominant[0][0] == dominant[1][0] and min(dominant[0][1], dominant[1][1]) >= 0.5
    payload = {"protocol": PROTOCOL, "performance_use_prohibited": True, "checkpoint_hashes": hashes, "episode_seeds": list(EPISODE_SEEDS), "stage_order": ["NO_LEGAL_TARGET_EVIDENCE", "NO_ATTACK_RANGE_ACQUISITION", "NO_LEGAL_GEOMETRY", "NO_COMMIT_IN_GEOMETRY", "NO_FOUR_STEP_HOLD", "POST_HOLD_NON_NEUTRAL_TERMINATION", "NEUTRALIZED"], "dominant_failure_by_training_seed": [{"seed": seed, "stage": stage, "fraction": rate} for seed, (stage, rate) in zip(TRAIN_SEEDS, dominant)], "verdict": "RESEARCH_PROBLEM_IDENTIFIED__READY_FOR_METHOD_DESIGN" if stable else "NO_IDENTIFIABLE_ALGORITHMIC_GAP__STOP_METHOD_HUNTING", "interpretation": "A stable mode requires the same exclusive failure stage to account for at least 50% of non-neutralized episodes in both frozen checkpoints. This is checkpoint-only localization, not a method comparison."}
    (OUT / "L4_STAGE_LOCALIZATION_MANIFEST.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__": main()
