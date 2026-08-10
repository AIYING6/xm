"""N2 development-only learnability pilot for the frozen N0/N1 mission.

This script intentionally trains one plain, no-graph MAPPO policy.  It is not
an implementation of a candidate paper method and its output is explicitly
non-evidentiary.  The standalone evaluator reports the frozen N1 RMTN180
outcome taxonomy rather than reusing legacy chain-establishment metrics.
"""

from __future__ import annotations

import csv
import argparse
import json
import math
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Callable

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    make_env,
    pcrf_r2_tensors,
    stack_graphs,
    train_ri_gmappo,
)
from envs.uav_intercept_3d_env import ACTION3D_TABLE, FLIGHT_ACTION_DIM  # noqa: E402


PROTOCOL_VERSION = "NEW_PROJECT_N2_LEARNABILITY_PILOT_V1"
TRAIN_SEEDS = (7201, 7202)
EVAL_SEEDS = tuple(range(730_000, 730_048))
UPDATES = 60
RMTN_HORIZON = 180
OUTCOMES = ("NEUTRALIZED", "COLLISION", "CONSTRAINT_FAILURE", "TARGET_ESCAPE", "TIMEOUT")


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def mission_cfg(seed: int, *, out_dir: Path, updates: int = UPDATES) -> RIGMAPPOConfig:
    """One transparent actor-only input baseline under the N1 contract."""
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=seed,
        num_envs=4,
        rollout_steps=128,
        updates=updates,
        hidden_dim=128,
        role_dim=8,
        intent_dim=8,
        graph_encoder="no_graph",
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
        lr=3e-4,
        entropy_coef=0.01,
        intent_coef=0.0,
        chain_aux_coef=0.0,
        role_gate_prior_strength=0.0,
        multi_relation_global_residual_weight=0.0,
        ppo_epochs=4,
        minibatch_graphs=256,
        # Training-time legacy chain evaluation is deliberately not an N2
        # decision metric.  The custom evaluator below is the frozen endpoint.
        eval_interval=1_000,
        eval_episodes=1,
        target_policy="evasive",
        communication_dropout_prob=0.0,
        message_delay_steps=0,
        radar_dropout_prob=0.0,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        mission_neutralization_enabled=True,
        engage_commit_hold_steps=4,
        target_escape_radius=35_000.0,
        mission_max_steps=360,
        failed_blue_agent=-1,
        node_failure_random_prob=0.0,
        node_failure_start_step=0,
        node_failure_duration_steps=0,
        attack_geometry_reward_weight=0.0,
        post_loss_chain_reclosure_reward_weight=0.0,
        device="cpu",
        out_dir=str(out_dir),
        save_interval=UPDATES,
        save_snapshots=False,
        validation_event_logging=False,
        run_id=f"vanilla_mappo_n2_seed{seed}",
        method_label="vanilla_mappo_n2",
        protocol_version=PROTOCOL_VERSION,
    )


def _action_id(turn: float, climb: float, accel: float) -> int:
    command = np.asarray((turn, climb, accel), dtype=np.float32)
    return int(np.argmin(np.linalg.norm(ACTION3D_TABLE - command[None, :], axis=1)))


def _angle_diff(a: float, b: float) -> float:
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi


def scripted_legal_heuristic(obs: np.ndarray) -> np.ndarray:
    """A transparent controller using *only* legal per-agent observation rows.

    It never reads the simulator state, graph, cache internals, an attack-window
    bit, or a communication indicator.  A zero target-relative vector is treated
    as unavailable target evidence, as required by the N1 actor contract.
    """
    actions = np.full(obs.shape[0], _action_id(0.0, 0.0, 0.0), dtype=np.int64)
    for i, row in enumerate(obs):
        rel = np.asarray(row[8:11], dtype=np.float32)
        target_norm = float(np.linalg.norm(rel))
        if target_norm < 1e-6:
            continue
        desired_heading = math.atan2(float(rel[1]), float(rel[0]))
        own_heading = math.atan2(float(row[4]), float(row[5]))
        desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2])) + 1e-6)
        own_gamma = math.atan2(float(row[6]), float(row[7]))
        flight = _action_id(
            1.0 if _angle_diff(desired_heading, own_heading) > 0.10 else (-1.0 if _angle_diff(desired_heading, own_heading) < -0.10 else 0.0),
            1.0 if desired_gamma - own_gamma > 0.08 else (-1.0 if desired_gamma - own_gamma < -0.08 else 0.0),
            1.0 if float(row[3]) < 0.90 else 0.0,
        )
        is_attacker = float(row[26]) > 0.5
        estimated_range = float(row[11])
        horizontal_alignment = math.cos(_angle_diff(desired_heading, own_heading))
        # This is an action decision only.  The environment independently checks
        # exact geometry and the 4-transition hold; a false positive commit is
        # therefore unable to create mission success.
        legal_commit_attempt = (
            is_attacker
            and 1_400.0 / 50_000.0 <= estimated_range <= 5_200.0 / 50_000.0
            and abs(float(rel[2])) <= 1_600.0 / 8_000.0
            and horizontal_alignment >= 0.90
        )
        actions[i] = flight + (FLIGHT_ACTION_DIM if legal_commit_attempt else 0)
    return actions


def random_no_commit(env_agents: int, rng: np.random.Generator) -> np.ndarray:
    return rng.integers(0, FLIGHT_ACTION_DIM, size=env_agents, dtype=np.int64)


def load_agent(cfg: RIGMAPPOConfig, checkpoint: Path) -> RIGMAPPOAgent:
    env = make_env(cfg, cfg.seed, training=False)
    _obs, _share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=env.share_obs_dim,
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
        graph_encoder=cfg.graph_encoder,
        graph_message_ablation=cfg.graph_message_ablation,
        graph_input_ablation=cfg.graph_input_ablation,
        use_intent_context=False,
        role_gate_prior_strength=cfg.role_gate_prior_strength,
        multi_relation_global_residual_weight=cfg.multi_relation_global_residual_weight,
        num_roles=max(4, int(np.max(graph["role"])) + 1),
    )
    agent.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True))
    agent.eval()
    return agent


def agent_actions(agent: RIGMAPPOAgent, obs: np.ndarray, share_obs: np.ndarray, graph: dict) -> np.ndarray:
    g = stack_graphs([graph])
    with torch.no_grad():
        actions, *_ = agent.get_action_and_value(
            torch.as_tensor(obs[None, ...], dtype=torch.float32),
            torch.as_tensor(g["node_feat"], dtype=torch.float32),
            torch.as_tensor(g["edge_feat"], dtype=torch.float32),
            torch.as_tensor(g["role"], dtype=torch.long),
            torch.as_tensor(g["adj"], dtype=torch.float32),
            torch.as_tensor(share_obs[None, ...], dtype=torch.float32),
            relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32),
            pcrf_r2=pcrf_r2_tensors(g, torch.device("cpu")),
            deterministic=True,
            intent_label=torch.as_tensor(g["intent_label"], dtype=torch.long),
        )
    return actions.squeeze(0).cpu().numpy()


def outcome(info: dict[str, float]) -> str:
    if float(info.get("target_neutralized", 0.0)) > 0.5:
        return "NEUTRALIZED"
    if float(info.get("collision", 0.0)) > 0.5:
        return "COLLISION"
    if float(info.get("constraint_violation", 0.0)) > 0.5:
        return "CONSTRAINT_FAILURE"
    if float(info.get("target_escape", 0.0)) > 0.5:
        return "TARGET_ESCAPE"
    return "TIMEOUT"


def evaluate_episode(
    cfg: RIGMAPPOConfig,
    seed: int,
    controller_name: str,
    controller: Callable[[np.ndarray, np.ndarray, dict], np.ndarray],
) -> dict[str, int | float | str]:
    env = make_env(cfg, seed, training=False)
    obs, share_obs, graph = env.reset()
    tau_outcome = "ACTIVE_UNNEUTRALIZED"
    tau_neutralized = False
    while True:
        obs, share_obs, graph, _reward, dones, info = env.step(controller(obs, share_obs, graph))
        if int(info["step"]) == RMTN_HORIZON:
            tau_neutralized = float(info.get("target_neutralized", 0.0)) > 0.5
            tau_outcome = outcome(info) if bool(np.all(dones)) else "ACTIVE_UNNEUTRALIZED"
        if bool(np.all(dones)):
            final = outcome(info)
            neutralized_by_tau = final == "NEUTRALIZED" and int(info["step"]) <= RMTN_HORIZON
            terminal_failure_by_tau = final in {"COLLISION", "CONSTRAINT_FAILURE", "TARGET_ESCAPE"} and int(info["step"]) <= RMTN_HORIZON
            if int(info["step"]) < RMTN_HORIZON:
                tau_outcome = final if final != "NEUTRALIZED" else "NEUTRALIZED"
                tau_neutralized = neutralized_by_tau
            return {
                "controller": controller_name,
                "episode_seed": seed,
                "final_outcome": final,
                "final_step": int(info["step"]),
                "neutralized_by_180": int(neutralized_by_tau),
                "terminal_failure_by_180": int(terminal_failure_by_tau),
                "active_unneutralized_at_180": int(not tau_neutralized and tau_outcome == "ACTIVE_UNNEUTRALIZED"),
                "tau_outcome": tau_outcome,
                "rmtn180_contribution": int(info["step"]) if neutralized_by_tau else RMTN_HORIZON,
            }


def summarize(rows: list[dict[str, int | float | str]]) -> list[dict[str, int | float | str]]:
    result = []
    for name in sorted({str(row["controller"]) for row in rows}):
        group = [row for row in rows if row["controller"] == name]
        item: dict[str, int | float | str] = {"controller": name, "episodes": len(group)}
        item["rmtn180"] = float(np.mean([float(r["rmtn180_contribution"]) for r in group]))
        item["neutralization_incidence180"] = float(np.mean([int(r["neutralized_by_180"]) for r in group]))
        item["terminal_failure_incidence180"] = float(np.mean([int(r["terminal_failure_by_180"]) for r in group]))
        item["active_unneutralized_probability180"] = float(np.mean([int(r["active_unneutralized_at_180"]) for r in group]))
        for label in OUTCOMES:
            item[f"final_{label.lower()}_incidence"] = float(np.mean([r["final_outcome"] == label for r in group]))
        result.append(item)
    return result


def write_csv(path: Path, rows: list[dict[str, int | float | str]]) -> None:
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen N2 development-only learnability pilot.")
    parser.add_argument(
        "--resume-incomplete",
        action="store_true",
        help="continue only an interrupted pilot lacking final evaluation outputs; never overwrites completed evidence",
    )
    args = parser.parse_args()
    output = ROOT / "results" / "new_project_n2_development_pilot"
    if output.exists() and not args.resume_incomplete:
        raise FileExistsError(f"refusing to overwrite development pilot: {output}")
    if args.resume_incomplete and (output / "N2_PILOT_VERDICT.json").exists():
        raise FileExistsError("pilot already has a final verdict; refusing a post-hoc rerun")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "performance_use_prohibited": True,
        "source_commit": source_commit(),
        "training_seeds": list(TRAIN_SEEDS),
        "evaluation_seeds": list(EVAL_SEEDS),
        "updates": UPDATES,
        "primary_metric": "RMTN180",
        "controller_ladder": ["random_no_commit", "scripted_legal_heuristic", "vanilla_mappo_n2"],
        "oracle_reference": "N1 timing calibration only; not executed, imitated, or selected here",
        "config": asdict(mission_cfg(TRAIN_SEEDS[0], out_dir=output / "template")),
    }
    manifest_path = output / "N2_PILOT_MANIFEST.json"
    if not manifest_path.exists():
        with manifest_path.open("x", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
    elif args.resume_incomplete:
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("protocol_version", "training_seeds", "evaluation_seeds", "updates", "primary_metric"):
            if existing.get(key) != manifest[key]:
                raise RuntimeError(f"incomplete pilot manifest mismatch: {key}")
        recovery_note = output / "N2_PILOT_INCOMPLETE_RECOVERY.json"
        if not recovery_note.exists():
            with recovery_note.open("x", encoding="utf-8") as handle:
                json.dump({
                    "reason": "interrupted execution before seed 7202 produced a checkpoint",
                    "action": "rerun only the missing development seed with the unchanged frozen manifest",
                    "source_commit": source_commit(),
                }, handle, indent=2, sort_keys=True)
                handle.write("\n")

    trained: list[tuple[str, RIGMAPPOConfig, RIGMAPPOAgent]] = []
    for seed in TRAIN_SEEDS:
        run_dir = output / f"vanilla_mappo_n2_seed{seed}"
        cfg = mission_cfg(seed, out_dir=run_dir)
        checkpoint = run_dir / "actor_critic_latest.pt"
        if not checkpoint.exists():
            print(f"N2 training start: seed={seed}, updates={UPDATES}", flush=True)
            train_ri_gmappo(cfg)
        else:
            print(f"N2 using existing completed development checkpoint: seed={seed}", flush=True)
        trained.append((f"vanilla_mappo_n2_seed{seed}", cfg, load_agent(cfg, checkpoint)))

    eval_cfg = mission_cfg(TRAIN_SEEDS[0], out_dir=output / "template", updates=1)
    records: list[dict[str, int | float | str]] = []
    for seed in EVAL_SEEDS:
        rng = np.random.default_rng(seed + 880_000)
        records.append(evaluate_episode(eval_cfg, seed, "random_no_commit", lambda o, s, g, rng=rng: random_no_commit(o.shape[0], rng)))
        records.append(evaluate_episode(eval_cfg, seed, "scripted_legal_heuristic", lambda o, s, g: scripted_legal_heuristic(o)))
        for name, _cfg, agent in trained:
            records.append(evaluate_episode(eval_cfg, seed, name, lambda o, s, g, agent=agent: agent_actions(agent, o, s, g)))
    summary = summarize(records)
    write_csv(output / "episode_outcomes.csv", records)
    write_csv(output / "summary.csv", summary)

    learned = [r for r in summary if str(r["controller"]).startswith("vanilla_mappo_n2_seed")]
    pooled = {
        "episodes": sum(int(r["episodes"]) for r in learned),
        "rmtn180": float(np.mean([float(r["rmtn180"]) for r in learned])),
        "neutralization_incidence180": float(np.mean([float(r["neutralization_incidence180"]) for r in learned])),
        "terminal_failure_incidence180": float(np.mean([float(r["terminal_failure_incidence180"]) for r in learned])),
    }
    verdict = "N2_GO" if (pooled["neutralization_incidence180"] > 0.0 and pooled["rmtn180"] < RMTN_HORIZON and pooled["neutralization_incidence180"] <= 0.879) else "N2_NO_GO"
    with (output / "N2_PILOT_VERDICT.json").open("x", encoding="utf-8") as handle:
        json.dump({"verdict": verdict, "pooled_vanilla_mappo": pooled, "summary": summary}, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"N2 development verdict": verdict, "pooled_vanilla_mappo": pooled}, indent=2), flush=True)


if __name__ == "__main__":
    main()
