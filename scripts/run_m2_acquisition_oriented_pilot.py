"""Frozen M2 Full-vs-B1 development pilot on corrected-contract L4.

This collector is intentionally separate from the historical stateless graph
collector: it carries explicit target/self history in the rollout buffer and
replays the exact pre-step state during PPO updates.  It is development-only.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from algorithms.ri_gmappo.acquisition_oriented import AcquisitionHistoryState, AcquisitionOrientedHybridPolicy  # noqa: E402
from algorithms.ri_gmappo.hybrid_action import TanhGaussianBernoulli  # noqa: E402
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR  # noqa: E402
from scripts import run_l4_corrected_contract_requalification as l4r  # noqa: E402
from scripts import run_new_project_l0_single_interceptor as l0  # noqa: E402

OUT = ROOT / "results" / "m2_acquisition_oriented_frozen_pilot"
TRAIN_SEEDS = (9201, 9202)
EVAL_SEEDS = tuple(range(890_000, 890_032))
UPDATES = 60
PROTOCOL = "M2_ACQUISITION_ORIENTED_FROZEN_TWO_SEED_PILOT_V1"


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def cfg(seed: int, out_dir: Path, updates: int = UPDATES):
    """The L4 corrected-contract task; no task or PPO setting is changed."""
    return replace(
        l4r.cfg(seed, out_dir, updates=updates),
        graph_encoder="no_graph",  # Graph path is unused by both M2 policy arms.
        protocol_version=PROTOCOL,
        run_id=f"m2_{seed}",
    )


def legal_evidence(obs: np.ndarray, run_cfg) -> np.ndarray:
    """Canonical actor-side availability: sensing OR delivered/cache-valid."""
    direct = obs[..., 18] > 0.5
    cache_age = obs[..., 30]
    cache_conf = obs[..., 31]
    max_age_norm = float(run_cfg.max_target_message_age_steps) / float(run_cfg.mission_max_steps)
    cache_valid = (cache_conf >= float(run_cfg.min_target_confidence)) & (cache_age <= max_age_norm + 1e-7)
    return direct | cache_valid


def role_ids(graph: dict) -> np.ndarray:
    # Recipient-specific graph: receiver is node 0 in each view.
    roles = np.asarray(graph["role"], dtype=np.int64)
    return roles[:, :, 0] if roles.ndim == 3 else roles[:, 0]


def attacker_mask(envs) -> np.ndarray:
    return np.asarray(
        [[typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR} for typ in env.config.blue_types] for env in envs],
        dtype=np.float32,
    )


class CentralCritic(nn.Module):
    def __init__(self, share_dim: int, num_roles: int, hidden_dim: int):
        super().__init__()
        self.num_roles = num_roles
        self.net = nn.Sequential(nn.Linear(share_dim + num_roles, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, 1))

    def forward(self, share: torch.Tensor, roles: torch.Tensor) -> torch.Tensor:
        onehot = torch.nn.functional.one_hot(roles.long().clamp(0, self.num_roles - 1), self.num_roles).to(share.dtype)
        return self.net(torch.cat([share, onehot], dim=-1)).squeeze(-1)


def masked_log_prob(dist: TanhGaussianBernoulli, action: torch.Tensor, attack: torch.Tensor) -> torch.Tensor:
    joint = dist.log_prob(action[..., :2], action[..., 2])
    commit_lp = dist.commit.log_prob(action[..., 2])
    return joint - commit_lp * (1.0 - attack)


def policy_step(policy, obs, previous_action, evidence, roles, state, attack, deterministic=False):
    logits, _progress, next_state = policy.forward_step(obs, previous_action, evidence, roles, state)
    dist = TanhGaussianBernoulli(logits[..., :2], logits[..., 2:4], logits[..., 4])
    continuous, commit, _ = dist.sample(deterministic=deterministic)
    action = torch.cat([continuous, commit.unsqueeze(-1)], dim=-1)
    # Only attacker has this semantic action.  PPO excludes masked commit LP.
    action[..., 2] = action[..., 2] * attack
    logp = masked_log_prob(dist, action, attack)
    return action, logp, dist.entropy(), next_state


def collect(policy, critic, envs, obs, share, graph, run_cfg, device, state, previous):
    data = {name: [] for name in ("obs", "share", "roles", "previous", "evidence", "target_state", "self_state", "actions", "logp", "values", "rewards", "dones", "attack")}
    attack_np = attacker_mask(envs)
    for _ in range(run_cfg.rollout_steps):
        roles_np, evidence_np = role_ids(graph), legal_evidence(obs, run_cfg)
        tensors = [torch.as_tensor(x, device=device) for x in (obs, previous, evidence_np, roles_np, attack_np, share)]
        obs_t, prev_t, evidence_t, roles_t, attack_t, share_t = tensors
        with torch.no_grad():
            action_t, logp_t, _entropy, next_state = policy_step(policy, obs_t.float(), prev_t.float(), evidence_t.bool(), roles_t.long(), state, attack_t.float())
            values_t = critic(share_t.float(), roles_t.long())
        action = action_t.cpu().numpy(); execute = action.copy(); execute[..., 2] = np.where(attack_np > 0.5, execute[..., 2], -1.0)
        next_obs = []; next_share = []; next_graph = []; rewards = []; dones = []
        done_env = []
        for idx, env in enumerate(envs):
            o, s, g, r, d, _info = env.step(execute[idx])
            ended = bool(np.all(d)); done_env.append(ended)
            if ended: o, s, g = env.reset()
            next_obs.append(o); next_share.append(s); next_graph.append(g); rewards.append(r[:, 0]); dones.append(d[:, 0])
        for name, value in {
            "obs": obs, "share": share, "roles": roles_np, "previous": previous, "evidence": evidence_np,
            "target_state": state.target.cpu().numpy(), "self_state": state.self_state.cpu().numpy(), "actions": action,
            "logp": logp_t.cpu().numpy(), "values": values_t.cpu().numpy(), "rewards": np.asarray(rewards, np.float32),
            "dones": np.asarray(dones, np.float32), "attack": attack_np,
        }.items(): data[name].append(value.copy())
        obs, share, graph = np.stack(next_obs), np.stack(next_share), l0.stack_graphs(next_graph) if hasattr(l0, "stack_graphs") else __import__("algorithms.ri_gmappo.simple_ri_gmappo", fromlist=["stack_graphs"]).stack_graphs(next_graph)
        previous = execute.astype(np.float32)
        reset = torch.as_tensor(np.asarray(done_env), dtype=torch.bool, device=device).unsqueeze(-1).unsqueeze(-1)
        zero_target, zero_self = torch.zeros_like(next_state.target), torch.zeros_like(next_state.self_state)
        state = AcquisitionHistoryState(target=torch.where(reset, zero_target, next_state.target), self_state=torch.where(reset, zero_self, next_state.self_state))
    with torch.no_grad():
        next_values = critic(torch.as_tensor(share, dtype=torch.float32, device=device), torch.as_tensor(role_ids(graph), device=device)).cpu().numpy()
    for name in data: data[name] = np.asarray(data[name])
    rewards, dones, values = data["rewards"], data["dones"], data["values"]
    adv = np.zeros_like(rewards); last = np.zeros_like(next_values)
    for t in reversed(range(run_cfg.rollout_steps)):
        nonterminal = 1.0 - dones[t]; nxt = next_values if t == run_cfg.rollout_steps - 1 else values[t + 1]
        delta = rewards[t] + run_cfg.gamma * nxt * nonterminal - values[t]
        last = delta + run_cfg.gamma * run_cfg.gae_lambda * nonterminal * last; adv[t] = last
    data.update(advantages=adv, returns=adv + values, next_obs=obs, next_share=share, next_graph=graph, next_state=state, next_previous=previous)
    return data


def update(policy, critic, optimizer, batch, run_cfg, device):
    total = int(np.prod(batch["rewards"].shape)); indexes = np.arange(total)
    flattened = {key: value.reshape(total, *value.shape[3:]) if value.ndim >= 3 else value.reshape(total) for key, value in batch.items() if key in {"obs", "share", "roles", "previous", "evidence", "target_state", "self_state", "actions", "logp", "advantages", "returns", "attack"}}
    adv = flattened["advantages"]; flattened["advantages"] = (adv - adv.mean()) / (adv.std() + 1e-8)
    losses = []
    for _ in range(run_cfg.ppo_epochs):
        np.random.shuffle(indexes)
        for start in range(0, total, run_cfg.minibatch_graphs):
            ind = indexes[start:start + run_cfg.minibatch_graphs]
            get = lambda name, dtype=torch.float32: torch.as_tensor(flattened[name][ind], dtype=dtype, device=device)
            state = AcquisitionHistoryState(target=get("target_state"), self_state=get("self_state"))
            logits, _p, _s = policy.forward_step(get("obs"), get("previous"), get("evidence", torch.bool), get("roles", torch.long), state)
            dist = TanhGaussianBernoulli(logits[..., :2], logits[..., 2:4], logits[..., 4])
            action, old_lp, attack, advantage = get("actions"), get("logp"), get("attack"), get("advantages")
            new_lp = masked_log_prob(dist, action, attack); ratio = torch.exp(new_lp - old_lp)
            policy_loss = -torch.minimum(ratio * advantage, ratio.clamp(1 - run_cfg.clip_coef, 1 + run_cfg.clip_coef) * advantage).mean()
            value = critic(get("share"), get("roles", torch.long)); value_loss = 0.5 * (value - get("returns")).square().mean()
            entropy = (dist.normal.entropy().sum(-1) + dist.commit.entropy() * attack).mean()
            loss = policy_loss + run_cfg.value_coef * value_loss - run_cfg.entropy_coef * entropy
            optimizer.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(list(policy.parameters()) + list(critic.parameters()), run_cfg.max_grad_norm); optimizer.step(); losses.append(float(loss.detach()))
    return float(np.mean(losses))


def evaluate(policy, run_cfg, device, method, episode_seeds):
    rows = []
    for seed in episode_seeds:
        env = l0.make_env(run_cfg, seed, training=False); obs, _share, graph = env.reset(); state = policy.core.initial_state(torch.as_tensor(obs, dtype=torch.float32, device=device)); previous = np.zeros((env.num_agents, 3), np.float32)
        attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}); evidence_step = None; range_step = None
        while True:
            roles, evidence = role_ids(graph), legal_evidence(obs, run_cfg); attack = np.asarray([typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR} for typ in env.config.blue_types], np.float32)
            with torch.no_grad(): action_t, _lp, _en, state = policy_step(policy, torch.as_tensor(obs, dtype=torch.float32, device=device), torch.as_tensor(previous, device=device), torch.as_tensor(evidence, device=device), torch.as_tensor(roles, device=device), state, torch.as_tensor(attack, device=device), deterministic=True)
            action = action_t.cpu().numpy(); action[:, 2] = np.where(attack > 0.5, action[:, 2], -1.0); previous = action.copy()
            if evidence[attacker] and evidence_step is None: evidence_step = env.step_count
            obs, _share, graph, _r, done, info = env.step(action)
            if np.linalg.norm(env.red_pos[0] - env.blue_pos[attacker]) <= env.config.blue_types[attacker].attack_range_max and range_step is None: range_step = env.step_count
            if bool(np.all(done)):
                neutral = l0.outcome(info) == "NEUTRALIZED"; no_acquisition = evidence_step is not None and range_step is None and not neutral
                rows.append({"method": method, "episode_seed": seed, "evidence_observed": int(evidence_step is not None), "attack_range_acquired": int(range_step is not None), "evidence_to_range_latency": int(range_step - evidence_step) if evidence_step is not None and range_step is not None else 180 - (evidence_step or 0), "no_attack_range_acquisition": int(no_acquisition), "neutralized": int(neutral), "rmtn180": int(info["step"]) if neutral else 180})
                break
    return rows


def run_method(method: str, seed: int, out: Path, device: torch.device, updates: int, episode_seeds):
    run_cfg = cfg(seed, out, updates); torch.manual_seed(seed); np.random.seed(seed)
    envs = [l0.make_env(run_cfg, seed * 1000 + i, training=True) for i in range(run_cfg.num_envs)]
    reset = [env.reset() for env in envs]; obs = np.stack([x[0] for x in reset]); share = np.stack([x[1] for x in reset]); graph = __import__("algorithms.ri_gmappo.simple_ri_gmappo", fromlist=["stack_graphs"]).stack_graphs([x[2] for x in reset])
    policy = AcquisitionOrientedHybridPolicy(obs.shape[-1], num_roles=4, hidden_dim=run_cfg.hidden_dim, full=method == "full").to(device)
    critic = CentralCritic(share.shape[-1], 4, run_cfg.hidden_dim).to(device); optimizer = torch.optim.Adam(list(policy.parameters()) + list(critic.parameters()), lr=run_cfg.lr)
    state = policy.core.initial_state(torch.as_tensor(obs, dtype=torch.float32, device=device)); previous = np.zeros((len(envs), envs[0].num_agents, 3), np.float32); log_rows = []
    for update_id in range(1, updates + 1):
        batch = collect(policy, critic, envs, obs, share, graph, run_cfg, device, state, previous); loss = update(policy, critic, optimizer, batch, run_cfg, device)
        obs, share, graph, state, previous = batch["next_obs"], batch["next_share"], batch["next_graph"], batch["next_state"], batch["next_previous"]
        log_rows.append({"update": update_id, "loss": loss, "target_history_nonzero": float(torch.count_nonzero(state.target) > 0)})
    out.mkdir(parents=True, exist_ok=False)
    torch.save({"policy": policy.state_dict(), "critic": critic.state_dict(), "config": asdict(run_cfg), "method": method, "seed": seed}, out / "checkpoint.pt")
    with (out / "train_log.csv").open("x", newline="", encoding="utf-8") as handle: writer = csv.DictWriter(handle, fieldnames=list(log_rows[0])); writer.writeheader(); writer.writerows(log_rows)
    return [{"training_seed": seed, **row} for row in evaluate(policy, run_cfg, device, method, episode_seeds)]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--device", default="cpu"); parser.add_argument("--smoke", action="store_true"); parser.add_argument("--output-root", type=Path, default=OUT); args = parser.parse_args()
    out_root = args.output_root
    if out_root.exists() and any(out_root.iterdir()): raise FileExistsError(f"refusing to overwrite {out_root}")
    device = torch.device(args.device); updates = 1 if args.smoke else UPDATES
    episode_seeds = EVAL_SEEDS[:1] if args.smoke else EVAL_SEEDS
    out_root.mkdir(parents=True)
    manifest = {"status": "M2_COLLECTOR_INTEGRATION_AND_FROZEN_TWO_SEED_PILOT", "performance_use_prohibited": True, "source_commit": source_commit(), "methods": ["full", "b1"], "training_seeds": list(TRAIN_SEEDS), "evaluation_seeds": list(episode_seeds), "updates": updates, "same_task_input_action_reward_critic_budget": True, "only_method_difference": "progress-conditioned target-history modulation versus direct fusion", "config": asdict(cfg(TRAIN_SEEDS[0], out_root / "template", updates))}
    (out_root / "PILOT_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = []
    for seed in TRAIN_SEEDS:
        for method in ("full", "b1"): rows.extend(run_method(method, seed, out_root / f"{method}_seed{seed}", device, updates, episode_seeds))
    with (out_root / "episode_records.csv").open("x", newline="", encoding="utf-8") as handle: writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for seed in TRAIN_SEEDS:
        for method in ("full", "b1"):
            group = [r for r in rows if r["method"] == method and r["training_seed"] == seed]
            evidence = [r for r in group if r["evidence_observed"]]
            summary.append({"training_seed": seed, "method": method, "episodes": len(group), "evidence_episodes": len(evidence), "acquisition_given_evidence": float(np.mean([r["attack_range_acquired"] for r in evidence])) if evidence else 0.0, "evidence_to_range_latency": float(np.mean([r["evidence_to_range_latency"] for r in evidence])) if evidence else 180.0, "no_attack_range_acquisition_fraction": float(np.mean([r["no_attack_range_acquisition"] for r in group])), "neutralization_rate": float(np.mean([r["neutralized"] for r in group])), "rmtn180": float(np.mean([r["rmtn180"] for r in group]))})
    with (out_root / "summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    per_seed = []
    for seed in TRAIN_SEEDS:
        full = next(row for row in summary if row["training_seed"] == seed and row["method"] == "full")
        b1 = next(row for row in summary if row["training_seed"] == seed and row["method"] == "b1")
        per_seed.append(full["acquisition_given_evidence"] > b1["acquisition_given_evidence"] and full["evidence_to_range_latency"] < b1["evidence_to_range_latency"] and full["no_attack_range_acquisition_fraction"] < b1["no_attack_range_acquisition_fraction"])
    verdict = "M2_PILOT_PASS__ACQUISITION_MECHANISM_SIGNAL_ESTABLISHED__READY_FOR_FORMAL_PROTOCOL" if all(per_seed) and any(next(row for row in summary if row["training_seed"] == seed and row["method"] == "full")["neutralization_rate"] > next(row for row in summary if row["training_seed"] == seed and row["method"] == "b1")["neutralization_rate"] for seed in TRAIN_SEEDS) else ("M2_PILOT_PARTIAL__SIGNAL_UNSTABLE__DIAGNOSE_EXISTING_RUNS_ONLY" if any(per_seed) else "M2_PILOT_NO_GO__ACQUISITION_CONDITIONING_NOT_SUPPORTED")
    (out_root / "PILOT_VERDICT.json").write_text(json.dumps({"verdict": verdict, "summary": summary, "performance_use_prohibited": True}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "summary": summary}, indent=2), flush=True)


if __name__ == "__main__": main()
