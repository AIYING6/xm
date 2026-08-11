"""Frozen M2R development pilot: identity-preserving residual Full vs B1."""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import torch

from algorithms.ri_gmappo.acquisition_residual import IdentityPreservingResidualPolicy
from algorithms.ri_gmappo.acquisition_oriented import AcquisitionHistoryState
from algorithms.ri_gmappo.simple_ri_gmappo import stack_graphs
from scripts import run_m2_acquisition_oriented_pilot as base
from scripts import run_new_project_l0_single_interceptor as l0

TRAIN_SEEDS = (9601, 9602)
EVAL_SEEDS = base.EVAL_SEEDS
UPDATES = 60
PROTOCOL = "M2R_IDENTITY_PRESERVING_RESIDUAL_TWO_SEED_PILOT_V1"
OUT = Path(__file__).resolve().parents[1] / "results" / "m2r_identity_preserving_frozen_pilot"


def cfg(seed, out_dir, updates=UPDATES):
    return replace(base.cfg(seed, out_dir, updates), protocol_version=PROTOCOL, run_id=f"m2r_{seed}")


def residual_stats(policy, progress, roles):
    residual = policy.residual(progress, roles)
    return float(residual.abs().max().detach()), float(residual.abs().mean().detach())


def evaluate(policy, run_cfg, device, method, episode_seeds):
    """Frozen endpoint evaluation plus non-evidentiary action-health traces."""
    rows = []
    for seed in episode_seeds:
        env = l0.make_env(run_cfg, seed, training=False)
        obs, _share, graph = env.reset()
        state = policy.core.initial_state(torch.as_tensor(obs, dtype=torch.float32, device=device))
        previous = np.zeros((env.num_agents, 3), np.float32)
        attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {base.ROLE_ATTACKER, base.ROLE_INTERCEPTOR})
        evidence_step = range_step = None
        evidence_actions, residual_magnitudes = [], []
        while True:
            roles, evidence = base.role_ids(graph), base.legal_evidence(obs, run_cfg)
            attack = np.asarray([typ.role in {base.ROLE_ATTACKER, base.ROLE_INTERCEPTOR} for typ in env.config.blue_types], np.float32)
            obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device)
            previous_t = torch.as_tensor(previous, dtype=torch.float32, device=device)
            evidence_t, roles_t = torch.as_tensor(evidence, device=device), torch.as_tensor(roles, device=device)
            with torch.no_grad():
                logits, progress, state = policy.forward_step(obs_t, previous_t, evidence_t, roles_t, state)
                dist = base.TanhGaussianBernoulli(logits[..., :2], logits[..., 2:4], logits[..., 4])
                continuous, commit, _ = dist.sample(deterministic=True)
                action_t = torch.cat([continuous, commit.unsqueeze(-1)], dim=-1)
                action_t[..., 2] = action_t[..., 2] * torch.as_tensor(attack, device=device)
                residual = policy.residual(progress, roles_t)[attacker]
            action = action_t.cpu().numpy()
            action[:, 2] = np.where(attack > 0.5, action[:, 2], -1.0)
            if evidence[attacker]:
                evidence_actions.append(action[attacker].copy())
                residual_magnitudes.append(float(residual.abs().mean().cpu()))
            previous = action.copy()
            if evidence[attacker] and evidence_step is None:
                evidence_step = env.step_count
            obs, _share, graph, _reward, done, info = env.step(action)
            if np.linalg.norm(env.red_pos[0] - env.blue_pos[attacker]) <= env.config.blue_types[attacker].attack_range_max and range_step is None:
                range_step = env.step_count
            if bool(np.all(done)):
                actions = np.asarray(evidence_actions, dtype=np.float32)
                residuals = np.asarray(residual_magnitudes, dtype=np.float32)
                neutral = l0.outcome(info) == "NEUTRALIZED"
                no_acquisition = evidence_step is not None and range_step is None and not neutral
                rows.append({
                    "method": method, "episode_seed": seed,
                    "evidence_observed": int(evidence_step is not None),
                    "attack_range_acquired": int(range_step is not None),
                    "evidence_to_range_latency": int(range_step - evidence_step) if evidence_step is not None and range_step is not None else 180 - (evidence_step or 0),
                    "no_attack_range_acquisition": int(no_acquisition), "neutralized": int(neutral),
                    "rmtn180": int(info["step"]) if neutral else 180,
                    "evidence_turn_std": float(actions[:, 0].std()) if len(actions) else 0.0,
                    "evidence_climb_std": float(actions[:, 1].std()) if len(actions) else 0.0,
                    "evidence_commit_rate": float((actions[:, 2] > 0).mean()) if len(actions) else 0.0,
                    "residual_abs_mean": float(residuals.mean()) if len(residuals) else 0.0,
                    "residual_bound_hit_fraction": float((residuals >= 0.249).mean()) if len(residuals) else 0.0,
                })
                break
    return rows


def run_method(method, seed, out, device, updates, episode_seeds):
    run_cfg = cfg(seed, out, updates); torch.manual_seed(seed); np.random.seed(seed)
    envs = [l0.make_env(run_cfg, seed * 1000 + i, training=True) for i in range(run_cfg.num_envs)]
    reset = [env.reset() for env in envs]; obs = np.stack([x[0] for x in reset]); share = np.stack([x[1] for x in reset]); graph = stack_graphs([x[2] for x in reset])
    policy = IdentityPreservingResidualPolicy(obs.shape[-1], full=method == "full").to(device)
    critic = base.CentralCritic(share.shape[-1], 4, run_cfg.hidden_dim).to(device)
    optimizer = torch.optim.Adam(list(policy.parameters()) + list(critic.parameters()), lr=run_cfg.lr)
    state = policy.core.initial_state(torch.as_tensor(obs, dtype=torch.float32, device=device)); previous = np.zeros((len(envs), envs[0].num_agents, 3), np.float32); logs = []
    for update_id in range(1, updates + 1):
        batch = base.collect(policy, critic, envs, obs, share, graph, run_cfg, device, state, previous)
        loss = base.update(policy, critic, optimizer, batch, run_cfg, device)
        obs, share, graph, state, previous = batch["next_obs"], batch["next_share"], batch["next_graph"], batch["next_state"], batch["next_previous"]
        roles = torch.as_tensor(base.role_ids(graph), device=device)
        with torch.no_grad():
            _fused, progress, _state = policy.core.forward_step(torch.as_tensor(obs, dtype=torch.float32, device=device), torch.as_tensor(previous, dtype=torch.float32, device=device), torch.as_tensor(base.legal_evidence(obs, run_cfg), device=device), state)
            residual_max, residual_mean = residual_stats(policy, progress, roles)
        logs.append({"update": update_id, "loss": loss, "residual_abs_max": residual_max, "residual_abs_mean": residual_mean, "target_history_nonzero": float(torch.count_nonzero(state.target) > 0)})
    out.mkdir(parents=True, exist_ok=False)
    torch.save({"policy": policy.state_dict(), "critic": critic.state_dict(), "config": asdict(run_cfg), "method": method, "seed": seed}, out / "checkpoint.pt")
    with (out / "train_log.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(logs[0])); writer.writeheader(); writer.writerows(logs)
    return [{"training_seed": seed, **row} for row in evaluate(policy, run_cfg, device, method, episode_seeds)]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--device", default="cpu"); parser.add_argument("--smoke", action="store_true"); parser.add_argument("--output-root", type=Path, default=OUT); parser.add_argument("--methods", nargs="+", choices=("full", "b1"), default=("full", "b1")); parser.add_argument("--seeds", nargs="+", type=int, default=TRAIN_SEEDS); args = parser.parse_args()
    if args.output_root.exists() and any(args.output_root.iterdir()): raise FileExistsError(f"refusing to overwrite {args.output_root}")
    updates, evaluation = (1, EVAL_SEEDS[:1]) if args.smoke else (UPDATES, EVAL_SEEDS)
    methods, seeds, device = tuple(args.methods), tuple(args.seeds), torch.device(args.device)
    args.output_root.mkdir(parents=True)
    manifest = {"status": "M2R_COLLECTOR_INTEGRATION_AND_FROZEN_TWO_SEED_PILOT", "source_commit": base.source_commit(), "methods": list(methods), "training_seeds": list(seeds), "evaluation_seeds": list(evaluation), "updates": updates, "performance_use_prohibited": True, "same_task_input_action_reward_critic_budget": True, "only_method_difference": "zero-initialized bounded progress residual on turn/climb means"}
    (args.output_root / "PILOT_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    records = []
    for seed in seeds:
        for method in methods: records.extend(run_method(method, seed, args.output_root / f"{method}_seed{seed}", device, updates, evaluation))
    with (args.output_root / "episode_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    summary=[]
    for seed in seeds:
        for method in methods:
            group=[r for r in records if r["training_seed"]==seed and r["method"]==method]; evidence=[r for r in group if r["evidence_observed"]]
            summary.append({"training_seed": seed, "method": method, "episodes": len(group), "evidence_episodes":len(evidence), "acquisition_given_evidence":float(np.mean([r["attack_range_acquired"] for r in evidence])) if evidence else 0., "evidence_to_range_latency":float(np.mean([r["evidence_to_range_latency"] for r in evidence])) if evidence else 180., "no_attack_range_acquisition_fraction":float(np.mean([r["no_attack_range_acquisition"] for r in group])), "neutralization_rate":float(np.mean([r["neutralized"] for r in group])), "rmtn180":float(np.mean([r["rmtn180"] for r in group])), "evidence_turn_std":float(np.mean([r["evidence_turn_std"] for r in group])), "evidence_climb_std":float(np.mean([r["evidence_climb_std"] for r in group])), "evidence_commit_rate":float(np.mean([r["evidence_commit_rate"] for r in group])), "residual_abs_mean":float(np.mean([r["residual_abs_mean"] for r in group])), "residual_bound_hit_fraction":float(np.mean([r["residual_bound_hit_fraction"] for r in group]))})
    with (args.output_root / "summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    print(json.dumps({"verdict":"M2R_SINGLE_RUN_COMPLETE__AGGREGATION_PENDING", "summary":summary},indent=2),flush=True)


if __name__ == "__main__": main()
