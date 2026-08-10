"""Read-only localization of the L1 heterogeneous coordination failure."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR  # noqa: E402
from scripts import run_l1_heterogeneous_reliable_development as l1  # noqa: E402
from scripts import run_new_project_l0_single_interceptor as base  # noqa: E402

OUT = ROOT / "results" / "l1_coordination_failure_localization"
SEEDS = tuple(range(821_000, 821_008))


def commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNAVAILABLE"


def load_pair(seed: int):
    rows = []
    for train_seed in l1.TRAIN_SEEDS:
        run = l1.OUT / f"l1_heterogeneous_reliable_seed{train_seed}"
        cfg = l1.cfg(train_seed, run, updates=1)
        agent = base.load_agent(cfg, run / "actor_critic_latest.pt")
        env = base.make_env(cfg, seed, training=False)
        obs, share, graph = env.reset()
        action = np.asarray(base.agent_actions(agent, obs, share, graph), dtype=np.float32).reshape(env.config.num_blue, 3)
        roles = [typ.role for typ in env.config.blue_types]
        for i, role in enumerate(roles):
            rows.append({"train_seed": train_seed, "episode_seed": seed, "role": role,
                         "turn": float(action[i, 0]), "climb": float(action[i, 1]),
                         "commit": float(action[i, 2] >= 0.0)})
    return rows


def run_counterfactual(train_seed: int, mode: str, seed: int) -> dict:
    run = l1.OUT / f"l1_heterogeneous_reliable_seed{train_seed}"
    cfg = l1.cfg(train_seed, run, updates=1)
    agent = base.load_agent(cfg, run / "actor_critic_latest.pt")
    env = base.make_env(cfg, seed, training=False)
    obs, share, graph = env.reset()
    attacker_ids = [i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}]
    entry = False
    while True:
        policy_action = np.asarray(base.agent_actions(agent, obs, share, graph), dtype=np.float32).reshape(env.config.num_blue, 3)
        action = policy_action.copy()
        if mode == "attacker_only":
            for i in range(env.config.num_blue):
                if i not in attacker_ids:
                    action[i] = (0.0, 0.0, -1.0)
        entry = entry or any(bool(env._in_true_standoff_envelope(i, env.config.blue_types[i])) for i in attacker_ids)
        obs, share, graph, _reward, dones, info = env.step(action)
        if bool(np.all(dones)):
            final = base.outcome(info)
            return {"train_seed": train_seed, "episode_seed": seed, "mode": mode,
                    "geometry_entry": int(entry), "neutralized": int(final == "NEUTRALIZED"),
                    "rmtn180": int(info["step"]) if final == "NEUTRALIZED" and int(info["step"]) <= 180 else 180,
                    "outcome": final}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    action_rows = []
    cf_rows = []
    for seed in SEEDS:
        action_rows.extend(load_pair(seed))
        for train_seed in l1.TRAIN_SEEDS:
            for mode in ("full_policy", "attacker_only"):
                cf_rows.append(run_counterfactual(train_seed, mode, seed))
    with (OUT / "initial_action_stats.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(action_rows[0])); w.writeheader(); w.writerows(action_rows)
    with (OUT / "counterfactual_outcomes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cf_rows[0])); w.writeheader(); w.writerows(cf_rows)
    stats = []
    for train_seed in l1.TRAIN_SEEDS:
        for role in sorted({r["role"] for r in action_rows}):
            group = [r for r in action_rows if r["train_seed"] == train_seed and r["role"] == role]
            stats.append({"train_seed": train_seed, "role": role, "n": len(group),
                          "turn_abs_mean": float(np.mean(np.abs([r["turn"] for r in group]))),
                          "climb_abs_mean": float(np.mean(np.abs([r["climb"] for r in group]))),
                          "commit_rate": float(np.mean([r["commit"] for r in group]))})
    summary = []
    for train_seed in l1.TRAIN_SEEDS:
        for mode in ("full_policy", "attacker_only"):
            group = [r for r in cf_rows if r["train_seed"] == train_seed and r["mode"] == mode]
            summary.append({"train_seed": train_seed, "mode": mode, "episodes": len(group),
                            "geometry_entry_rate": float(np.mean([r["geometry_entry"] for r in group])),
                            "neutralization_rate": float(np.mean([r["neutralized"] for r in group])),
                            "rmtn180": float(np.mean([r["rmtn180"] for r in group]))})
    payload = {"status": "L1_COORDINATION_FAILURE_LOCALIZATION_COMPLETE", "performance_use_prohibited": True,
               "source_commit": commit(), "initial_action_stats": stats, "counterfactual_summary": summary,
               "interpretation": "read-only localization; no architecture or training decision"}
    (OUT / "L1_COORDINATION_FAILURE_LOCALIZATION.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
