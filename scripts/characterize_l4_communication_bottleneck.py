"""Paired, checkpoint-only L4 communication bottleneck characterization."""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import replace
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR
from scripts import run_l4_corrected_contract_requalification as l4r
from scripts import run_new_project_l0_single_interceptor as l0

OUT = ROOT / "results" / "l4_bottleneck_characterization"
CHECKPOINT_ROOT = ROOT / "results" / "l4_corrected_contract_requalification"
TRAIN_SEEDS = (8901, 8902)
EPISODE_SEEDS = tuple(range(890_000, 890_032))
PROTOCOL = "L4_BOTTLENECK_CHARACTERIZATION_V1"
CONDITIONS = {
    "l4_frozen": {"communication_range_scale": 0.5, "communication_dropout_prob": 0.3, "message_delay_steps": 8},
    "no_delay": {"communication_range_scale": 0.5, "communication_dropout_prob": 0.3, "message_delay_steps": 0},
    "no_dropout": {"communication_range_scale": 0.5, "communication_dropout_prob": 0.0, "message_delay_steps": 8},
    "full_range": {"communication_range_scale": 1.0, "communication_dropout_prob": 0.3, "message_delay_steps": 8},
    "ideal_communication": {"communication_range_scale": 1.0, "communication_dropout_prob": 0.0, "message_delay_steps": 0},
}


def eval_cfg(train_seed: int, condition: str):
    return replace(l4r.cfg(train_seed, OUT / "template", updates=1), **CONDITIONS[condition], protocol_version=PROTOCOL, run_id=f"l4_characterization_{condition}_seed{train_seed}")


def episode(cfg, episode_seed: int, agent) -> dict[str, object]:
    env = l0.make_env(cfg, episode_seed, training=False)
    obs, share, graph = env.reset()
    attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR})
    first_evidence = first_geometry = None; max_dwell = dwell = max_commit_hold = 0
    while True:
        action = np.asarray(l0.agent_actions(agent, obs, share, graph), dtype=np.float32).reshape(env.num_agents, 3)
        for i, typ in enumerate(env.config.blue_types):
            if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}: action[i, 2] = -1.0
        obs, share, graph, _reward, dones, info = env.step(action)
        if first_evidence is None and env._has_fresh_target_cache(attacker): first_evidence = int(env.step_count)
        valid = bool(env._in_true_standoff_envelope(attacker, env.config.blue_types[attacker]))
        dwell = dwell + 1 if valid else 0; max_dwell = max(max_dwell, dwell)
        max_commit_hold = max(max_commit_hold, int(env.engage_commit_hold))
        if first_geometry is None and valid: first_geometry = int(env.step_count)
        if bool(np.all(dones)):
            final = l0.outcome(info)
            return {"episode_seed": episode_seed, "final_outcome": final, "neutralized": int(final == "NEUTRALIZED"), "terminal_step": int(info["step"]), "first_attacker_target_evidence_step": first_evidence, "first_attack_geometry_step": first_geometry, "max_geometry_dwell_steps": max_dwell, "max_engage_commit_hold": max_commit_hold, "final_target_cache_age": int(env._local_target_cache_age(attacker)) if env._has_fresh_target_cache(attacker) else None}


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()): raise FileExistsError(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True, exist_ok=True); rows = []; hashes = {}
    for train_seed in TRAIN_SEEDS:
        ckpt = CHECKPOINT_ROOT / f"l4_corrected_contract_seed{train_seed}" / "actor_critic_latest.pt"
        if not ckpt.exists(): raise FileNotFoundError(ckpt)
        hashes[str(train_seed)] = hashlib.sha256(ckpt.read_bytes()).hexdigest()
        agent = l0.load_agent(eval_cfg(train_seed, "l4_frozen"), ckpt)
        for condition in CONDITIONS:
            current = eval_cfg(train_seed, condition)
            for episode_seed in EPISODE_SEEDS: rows.append({"training_seed": train_seed, "condition": condition, **episode(current, episode_seed, agent)})
    with (OUT / "paired_episode_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for train_seed in TRAIN_SEEDS:
        frozen = sorted([r for r in rows if r["training_seed"] == train_seed and r["condition"] == "l4_frozen"], key=lambda r: r["episode_seed"])
        for condition in CONDITIONS:
            group = sorted([r for r in rows if r["training_seed"] == train_seed and r["condition"] == condition], key=lambda r: r["episode_seed"])
            summary.append({"training_seed": train_seed, "condition": condition, "episodes": len(group), "neutralization_rate": float(np.mean([r["neutralized"] for r in group])), "mean_terminal_step": float(np.mean([r["terminal_step"] for r in group])), "mean_first_evidence_step": float(np.mean([r["first_attacker_target_evidence_step"] or 181 for r in group])), "mean_max_geometry_dwell": float(np.mean([r["max_geometry_dwell_steps"] for r in group])), "paired_neutralization_delta_vs_l4": float(np.mean([b["neutralized"] - a["neutralized"] for a, b in zip(frozen, group)]) )})
    with (OUT / "condition_summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    payload = {"protocol": PROTOCOL, "performance_use_prohibited": True, "checkpoint_hashes": hashes, "training_seeds": list(TRAIN_SEEDS), "paired_episode_seeds": list(EPISODE_SEEDS), "conditions": CONDITIONS, "interpretation_boundary": "Checkpoint-only sensitivity diagnostic; no training-time causal conclusion or method selection.", "status": "L4_BOTTLENECK_CHARACTERIZATION_COMPLETE__METHOD_SELECTION_REQUIRES_SEPARATE_AUTHORIZATION"}
    (OUT / "L4_BOTTLENECK_CHARACTERIZATION_MANIFEST.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__": main()
