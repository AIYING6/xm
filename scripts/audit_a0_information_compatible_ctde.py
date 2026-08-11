"""A0 read-only audit of privileged centralized-critic mismatch.

This is an evaluator-only counterfactual.  It never changes an environment
transition, checkpoint, policy action, or actor-visible tensor.  At selected
states where the Attacker has no legal target evidence, it changes only the
training-only global target estimate consumed by ``share_obs`` and records the
central critic's value/one-step TD change after asserting that every Attacker
actor input tensor is byte-identical.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import stack_graphs  # noqa: E402
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR  # noqa: E402
from scripts import run_l4_corrected_contract_requalification as l4r  # noqa: E402
from scripts import run_new_project_l0_single_interceptor as l0  # noqa: E402
from scripts.run_new_project_n2_development_pilot import agent_actions  # noqa: E402


PROTOCOL = "A0_INFORMATION_COMPATIBLE_CTDE_QUALIFICATION_V1"
TRAIN_SEEDS = (8901, 8902)
EPISODE_SEEDS = tuple(range(890_000, 890_032))


def digest(*arrays: np.ndarray) -> str:
    """Hash exactly the tensors supplied to one recipient actor."""
    hasher = hashlib.sha256()
    for array in arrays:
        contiguous = np.ascontiguousarray(array)
        hasher.update(str(contiguous.dtype).encode("ascii"))
        hasher.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
        hasher.update(contiguous.tobytes())
    return hasher.hexdigest()


def attacker_actor_digest(obs: np.ndarray, graph: dict[str, np.ndarray], attacker: int) -> str:
    return digest(
        obs[attacker],
        graph["node_feat"][attacker],
        graph["edge_feat"][attacker],
        graph["role"][attacker],
        graph["adj"][attacker],
        graph["relation_adj"][attacker],
    )


def critic_value(agent, share: np.ndarray, graph: dict[str, np.ndarray], attacker: int) -> float:
    with torch.no_grad():
        values = agent.critic_value(
            torch.as_tensor(share[None, ...], dtype=torch.float32),
            torch.as_tensor(graph["role"][None, ...], dtype=torch.long),
        )
    return float(values[0, attacker].cpu())


def alternate_estimate(env) -> tuple[np.ndarray, np.ndarray]:
    """Return a deterministic, physical-domain alternative global estimate.

    This is not a second simulated state: the target dynamics and all actor
    inputs are restored unchanged.  The perturbation exists solely to test
    whether the training-only critic consumes a target estimate inaccessible to
    this Attacker.
    """
    assert env.last_detected_target_pos is not None
    base_pos = env.last_detected_target_pos.copy()
    base_vel = (env.last_detected_target_vel.copy() if env.last_detected_target_vel is not None else np.zeros(3, dtype=np.float32))
    shift = np.asarray((0.23 * env.config.world_radius, -0.19 * env.config.world_radius, 0.12 * env.config.max_altitude), dtype=np.float32)
    pos = base_pos + shift
    horizontal = float(np.linalg.norm(pos[:2]))
    max_horizontal = 0.80 * env.config.world_radius
    if horizontal > max_horizontal:
        pos[:2] *= max_horizontal / horizontal
    pos[2] = float(np.clip(pos[2], 0.05 * env.config.max_altitude, 0.95 * env.config.max_altitude))
    return pos.astype(np.float32), (-base_vel).astype(np.float32)


def run_checkpoint(cfg, checkpoint: Path, train_seed: int) -> list[dict[str, object]]:
    agent = l0.load_agent(cfg, checkpoint)
    rows: list[dict[str, object]] = []
    for episode_seed in EPISODE_SEEDS:
        env = l0.make_env(cfg, episode_seed, training=False)
        obs, share, graph = env.reset()
        attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR})
        while True:
            trigger = bool(env.last_detected_target_pos is not None and not env._has_fresh_target_cache(attacker))
            base_value = critic_value(agent, share, graph, attacker)
            base_actor_hash = attacker_actor_digest(obs, graph, attacker)
            cf_value = None
            actor_hash_match = None
            if trigger:
                saved_pos = env.last_detected_target_pos.copy()
                saved_vel = env.last_detected_target_vel.copy() if env.last_detected_target_vel is not None else None
                try:
                    env.last_detected_target_pos, env.last_detected_target_vel = alternate_estimate(env)
                    cf_obs, cf_share, cf_graph = env._get_obs(), env._get_share_obs(), env._get_graph_obs()
                    actor_hash_match = base_actor_hash == attacker_actor_digest(cf_obs, cf_graph, attacker)
                    if not actor_hash_match:
                        raise AssertionError("A0 counterfactual altered a recipient actor input")
                    cf_value = critic_value(agent, cf_share, cf_graph, attacker)
                finally:
                    env.last_detected_target_pos = saved_pos
                    env.last_detected_target_vel = saved_vel

            action = np.asarray(agent_actions(agent, obs, share, graph), dtype=np.float32).reshape(env.num_agents, 3)
            for i, typ in enumerate(env.config.blue_types):
                if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
                    action[i, 2] = -1.0
            next_obs, next_share, next_graph, reward, dones, info = env.step(action)
            next_value = 0.0 if bool(dones[attacker, 0]) else critic_value(agent, next_share, next_graph, attacker)
            td = float(reward[attacker, 0]) + cfg.gamma * next_value - base_value
            if trigger:
                td_cf = float(reward[attacker, 0]) + cfg.gamma * next_value - float(cf_value)
                rows.append(
                    {
                        "training_seed": train_seed,
                        "episode_seed": episode_seed,
                        "step": int(info["step"]) - 1,
                        "actor_target_cache_valid": 0,
                        "global_target_estimate_exists": 1,
                        "actor_input_hash": base_actor_hash,
                        "actor_input_invariant": int(bool(actor_hash_match)),
                        "central_value": base_value,
                        "counterfactual_central_value": float(cf_value),
                        "absolute_value_shift": abs(base_value - float(cf_value)),
                        "one_step_td": td,
                        "counterfactual_one_step_td": td_cf,
                        "td_sign_conflict": int(td * td_cf < 0.0),
                    }
                )
            obs, share, graph = next_obs, next_share, next_graph
            if bool(np.all(dones)):
                break
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "a0_information_compatible_ctde_audit")
    parser.add_argument("--checkpoint-root", type=Path, default=ROOT / "results" / "l4_corrected_contract_requalification")
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    hashes: dict[str, str] = {}
    for seed in TRAIN_SEEDS:
        checkpoint = args.checkpoint_root / f"l4_corrected_contract_seed{seed}" / "actor_critic_latest.pt"
        if not checkpoint.exists():
            raise FileNotFoundError(checkpoint)
        hashes[str(seed)] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        rows.extend(run_checkpoint(l4r.cfg(seed, out / "template", updates=1), checkpoint, seed))
    if not rows:
        raise RuntimeError("No actor-blind / global-estimate-visible decision states found")
    with (out / "counterfactual_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    all_values = np.asarray([float(row["central_value"]) for row in rows], dtype=np.float64)
    value_sd = float(np.std(all_values))
    summaries = []
    for seed in TRAIN_SEEDS:
        group = [row for row in rows if row["training_seed"] == seed]
        shifts = np.asarray([float(row["absolute_value_shift"]) for row in group], dtype=np.float64)
        conflicts = float(np.mean([int(row["td_sign_conflict"]) for row in group]))
        summaries.append({
            "training_seed": seed,
            "actor_blind_global_visible_states": len(group),
            "actor_input_invariance_rate": float(np.mean([int(row["actor_input_invariant"]) for row in group])),
            "median_absolute_value_shift": float(np.median(shifts)),
            "p90_absolute_value_shift": float(np.quantile(shifts, 0.90)),
            "td_sign_conflict_rate": conflicts,
        })
    with (out / "summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)

    normalized_medians = [row["median_absolute_value_shift"] / max(value_sd, 1e-8) for row in summaries]
    material = all(row["actor_blind_global_visible_states"] >= 20 and row["actor_input_invariance_rate"] == 1.0 for row in summaries) and min(normalized_medians) >= 0.10
    payload = {
        "protocol": PROTOCOL,
        "performance_use_prohibited": True,
        "checkpoint_hashes": hashes,
        "training_seeds": list(TRAIN_SEEDS),
        "episode_seeds": list(EPISODE_SEEDS),
        "counterfactual": "Change only global last_detected_target estimate while Attacker has no valid target cache; assert Attacker actor tensors are identical; do not execute the altered environment.",
        "value_standard_deviation_over_selected_states": value_sd,
        "summary": summaries,
        "material_mismatch_threshold": "Each checkpoint: >=20 selected states, exact actor-input invariance, median |delta Vcentral| >= 0.10 * selected-state SD(Vcentral).",
        "phenomenon_verdict": "A0_PRIVILEGED_CRITIC_MISMATCH_OBSERVED" if material else "A0_PRIVILEGED_CRITIC_MISMATCH_NOT_MATERIAL",
        "scope_limit": "This tests critic-information sensitivity and a one-step TD proxy, not a new advantage estimator or a policy-performance claim.",
    }
    (out / "A0_INFORMATION_COMPATIBLE_CTDE_AUDIT_MANIFEST.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
