#!/usr/bin/env python3
"""P18: can a learned policy capture the attitude-coupling gain that hand rules cannot?

P16 measured the single-nose conflict (conflict rate 1.000, median Pareto loss 0.780).
P17 tested hand-written policies: the coupled rule beat the best fixed schedule by
3-5x in the 70-110 deg band, but reached only 0 delivered messages in the
120-180 deg band where the dynamic-programming oracle reaches 57-60.

This script trains a compact PPO on the coupling task and tests the four gates that
were frozen in configs/p18_attitude_coupled_learning_20260910.json *before* running.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.attitude_coupled_relay_env import (  # noqa: E402
    AttitudeCoupledRelayConfig,
    AttitudeCoupledRelayEnv,
)

TURN = (-1, 0, 1)


def wrap(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


# ---------------------------------------------------------------- PPO


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int, hidden: int):
        super().__init__()
        self.actor = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, action_dim),
        )
        self.critic = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1),
        )

    def forward(self, obs):
        return self.actor(obs), self.critic(obs).squeeze(-1)


def train_one_seed(cfg: dict, seed: int, device: torch.device):
    torch.manual_seed(seed)
    np.random.seed(seed)
    t = cfg["training"]
    envs = [
        AttitudeCoupledRelayEnv(AttitudeCoupledRelayConfig(seed=seed * 1000 + i))
        for i in range(t["parallel_envs"])
    ]
    obs = np.stack([e.reset()[0] for e in envs])
    net = ActorCritic(envs[0].obs_dim, envs[0].action_dim, t["hidden_dim"]).to(device)
    opt = optim.Adam(net.parameters(), lr=t["lr"], eps=1e-5)

    n_envs, obs_dim, horizon = t["parallel_envs"], envs[0].obs_dim, t["rollout_steps"]
    for _ in range(t["updates"]):
        o_buf, a_buf, lp_buf, r_buf, d_buf, v_buf = [], [], [], [], [], []
        for _ in range(horizon):
            with torch.no_grad():
                logits, value = net(torch.as_tensor(obs, dtype=torch.float32, device=device))
                dist = Categorical(logits=logits)
                act = dist.sample()
                lp = dist.log_prob(act)
            o_buf.append(obs.copy())
            a_buf.append(act.cpu().numpy())
            lp_buf.append(lp.cpu().numpy())
            v_buf.append(value.cpu().numpy())
            r, d, nobs = [], [], []
            for i, env in enumerate(envs):
                ob, _, _, rew, dn, _ = env.step(int(act[i].item()))
                if dn[0] > 0.5:
                    ob = env.reset()[0]
                nobs.append(ob)
                r.append(rew[0])
                d.append(dn[0])
            r_buf.append(np.asarray(r, dtype=np.float32))
            d_buf.append(np.asarray(d, dtype=np.float32))
            obs = np.stack(nobs)

        with torch.no_grad():
            _, last_v = net(torch.as_tensor(obs, dtype=torch.float32, device=device))
            last_v = last_v.cpu().numpy()
        rew = np.asarray(r_buf)
        dones = np.asarray(d_buf)
        vals = np.asarray(v_buf)
        adv = np.zeros_like(rew)
        last = np.zeros(n_envs, dtype=np.float32)
        for s in reversed(range(horizon)):
            nxt = last_v if s == horizon - 1 else vals[s + 1]
            nonterm = 1.0 - dones[s]
            delta = rew[s] + t["gamma"] * nxt * nonterm - vals[s]
            last = delta + t["gamma"] * t["gae_lambda"] * nonterm * last
            adv[s] = last
        ret = adv + vals

        o = torch.as_tensor(np.asarray(o_buf).reshape(-1, obs_dim), dtype=torch.float32, device=device)
        a = torch.as_tensor(np.asarray(a_buf).reshape(-1), dtype=torch.long, device=device)
        olp = torch.as_tensor(np.asarray(lp_buf).reshape(-1), dtype=torch.float32, device=device)
        adv_f = torch.as_tensor(adv.reshape(-1), dtype=torch.float32, device=device)
        ret_f = torch.as_tensor(ret.reshape(-1), dtype=torch.float32, device=device)
        adv_f = (adv_f - adv_f.mean()) / (adv_f.std() + 1e-8)
        idx = np.arange(o.shape[0])
        for _ in range(t["ppo_epochs"]):
            np.random.shuffle(idx)
            for start in range(0, len(idx), t["minibatch"]):
                mb = idx[start:start + t["minibatch"]]
                logits, value = net(o[mb])
                dist = Categorical(logits=logits)
                nlp = dist.log_prob(a[mb])
                ratio = (nlp - olp[mb]).exp()
                pg = -torch.min(
                    adv_f[mb] * ratio,
                    adv_f[mb] * torch.clamp(ratio, 1 - t["clip_coef"], 1 + t["clip_coef"]),
                ).mean()
                vl = 0.5 * (ret_f[mb] - value).pow(2).mean()
                ent = dist.entropy().mean()
                loss = pg + t["value_coef"] * vl - t["entropy_coef"] * ent
                opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(net.parameters(), 0.5)
                opt.step()
    net.eval()
    return net


# ---------------------------------------------------------------- evaluation


def force_geometry(env: AttitudeCoupledRelayEnv, sep_deg: float):
    obs, _, _ = env.reset()
    env.target_bearing = 0.0
    env.relay_bearing = math.radians(sep_deg)
    env.separation = math.radians(abs(sep_deg))
    env.heading = 0.0
    env.cache_age = env.ttl + 1
    env.step_count = 0
    env.delivered = 0
    env.done = False
    # keep positions consistent so a moving config does not overwrite the bearings
    cfg = env.config
    env.agent_pos = np.zeros(2)
    env.target_pos = cfg.target_distance * np.asarray([math.cos(0.0), math.sin(0.0)])
    env.relay_pos = cfg.relay_distance * np.asarray(
        [math.cos(env.relay_bearing), math.sin(env.relay_bearing)]
    )
    return env._obs()


def evaluate_learned(net, cfg, separations, device):
    env = AttitudeCoupledRelayEnv(AttitudeCoupledRelayConfig(seed=12345))
    out = []
    for sep in separations:
        obs = force_geometry(env, sep)
        while not env.done:
            with torch.no_grad():
                logits, _ = net(torch.as_tensor(obs[None, :], dtype=torch.float32, device=device))
            obs, _, _, _, _, _ = env.step(int(torch.argmax(logits, dim=-1).item()))
        out.append(float(env.delivered))
    return out


def run_scripted(policy, cfg, separations):
    env = AttitudeCoupledRelayEnv(AttitudeCoupledRelayConfig(seed=12345))
    out = []
    for sep in separations:
        obs = force_geometry(env, sep)
        while not env.done:
            obs, _, _, _, _, _ = env.step(policy(env))
        out.append(float(env.delivered))
    return out


def pol_always_target(env):
    return 0 if wrap(env.target_bearing - env.heading) > 0 else 2


def pol_always_relay(env):
    return 0 if wrap(env.relay_bearing - env.heading) > 0 else 2


def pol_fixed_alternate(env, period=4):
    desired = env.target_bearing if (env.step_count // period) % 2 == 0 else env.relay_bearing
    return 0 if wrap(desired - env.heading) > 0 else 2


def pol_hand_coupled(env):
    d = abs(wrap(env.target_bearing - env.relay_bearing))
    if d <= env.half_fov + env.half_link:
        lo = max(env.target_bearing - env.half_fov, env.relay_bearing - env.half_link)
        hi = min(env.target_bearing + env.half_fov, env.relay_bearing + env.half_link)
        desired = 0.5 * (lo + hi)
    else:
        desired = env.target_bearing if env.cache_age < env.ttl - 1 else env.relay_bearing
    return 0 if wrap(desired - env.heading) > 0 else 2


def oracle_dp(sep_deg: float, cfg: dict) -> int:
    e = cfg["environment"]
    n_head = 72
    grid = np.linspace(-math.pi, math.pi, n_head, endpoint=False)
    half_fov = math.radians(e["radar_half_fov_deg"])
    half_link = math.radians(e["link_half_angle_deg"])
    ttl = e["cache_ttl_steps"]
    horizon = e["horizon_steps"]
    tb, rb = 0.0, math.radians(sep_deg)
    det = np.abs(((grid - tb + math.pi) % (2 * math.pi)) - math.pi) <= half_fov
    lnk = np.abs(((grid - rb + math.pi) % (2 * math.pi)) - math.pi) <= half_link
    step_idx = 1
    ages = ttl + 2
    value = np.zeros((n_head, ages))
    for _ in range(horizon):
        nv = np.zeros((n_head, ages))
        for h in range(n_head):
            for a in range(ages):
                best = -1.0
                for dh in range(-step_idx, step_idx + 1):
                    h2 = (h + dh) % n_head
                    a2 = 0 if det[h2] else min(a + 1, ttl + 1)
                    reward = 1.0 if (a2 <= ttl and lnk[h2]) else 0.0
                    cand = reward + value[h2, a2]
                    if cand > best:
                        best = cand
                nv[h, a] = best
        value = nv
    start = int(np.argmin(np.abs(((grid - 0.0 + math.pi) % (2 * math.pi)) - math.pi)))
    return int(round(value[start, ttl + 1]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    if cfg["protocol"] != "P18-ATTITUDE-COUPLED-LEARNING-V1":
        raise ValueError("protocol mismatch")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_grid = list(range(0, 181, 20))
    holdout_grid = list(range(10, 181, 20))
    full_grid = list(range(0, 181, 10))

    print(f"device={device}")
    learned_runs = []
    for seed in cfg["training"]["seeds"]:
        net = train_one_seed(cfg, seed, device)
        full = evaluate_learned(net, cfg, full_grid, device)
        learned_runs.append({"seed": seed, "full_grid": full})
        print(f"seed {seed}: mean delivered over grid = {np.mean(full):.2f}")

    learned = np.mean([r["full_grid"] for r in learned_runs], axis=0)

    baselines = {
        "fixed_always_target": run_scripted(pol_always_target, cfg, full_grid),
        "fixed_always_relay": run_scripted(pol_always_relay, cfg, full_grid),
        "fixed_alternate_4": run_scripted(pol_fixed_alternate, cfg, full_grid),
        "hand_coupled_heuristic": run_scripted(pol_hand_coupled, cfg, full_grid),
    }
    oracle = [oracle_dp(s, cfg) for s in full_grid]

    best_fixed = np.max(
        np.stack([baselines["fixed_always_target"], baselines["fixed_always_relay"],
                  baselines["fixed_alternate_4"]]), axis=0
    )
    band = [i for i, s in enumerate(full_grid) if 70 <= s <= 110]

    learned_mean = float(np.mean(learned))
    best_fixed_mean = float(np.mean(best_fixed))
    oracle_mean = float(np.mean(oracle))
    hand_band = float(np.mean([baselines["hand_coupled_heuristic"][i] for i in band]))
    learned_band = float(np.mean([learned[i] for i in band]))

    learned_train = float(np.mean([learned[full_grid.index(s)] for s in train_grid]))
    learned_hold = float(np.mean([learned[full_grid.index(s)] for s in holdout_grid]))

    checks = {
        "G1_beats_best_fixed_by_20pct": learned_mean >= 1.20 * best_fixed_mean,
        "G2_beats_hand_coupled_in_conflict_band": learned_band >= 1.20 * hand_band,
        "G3_reaches_80pct_of_oracle": learned_mean >= 0.80 * oracle_mean,
        "G4_holds_out": learned_hold >= 0.90 * learned_train,
    }
    result = {
        "protocol": cfg["protocol"],
        "verdict": "P18_PASS" if all(checks.values()) else "P18_FAIL",
        "device": str(device),
        "grid_deg": full_grid,
        "learned_mean": learned_mean,
        "learned_by_seed_mean": [float(np.mean(r["full_grid"])) for r in learned_runs],
        "best_fixed_mean": best_fixed_mean,
        "hand_coupled_mean": float(np.mean(baselines["hand_coupled_heuristic"])),
        "oracle_mean": oracle_mean,
        "conflict_band_70_110": {
            "learned_mean": learned_band,
            "hand_coupled_mean": hand_band,
        },
        "learned_train_range_mean": learned_train,
        "learned_heldout_range_mean": learned_hold,
        "curve_learned": list(map(float, learned)),
        "curve_best_fixed": list(map(float, best_fixed)),
        "curve_hand_coupled": list(map(float, baselines["hand_coupled_heuristic"])),
        "curve_oracle": list(map(float, oracle)),
        "checks": checks,
        "environment_steps": (
            cfg["training"]["updates"] * cfg["training"]["parallel_envs"]
            * cfg["training"]["rollout_steps"] * len(cfg["training"]["seeds"])
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "P18_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print()
    print("sep | learned | best_fixed | hand_coupled | oracle")
    for i, s in enumerate(full_grid):
        print(f"{s:>3} | {learned[i]:>7.1f} | {best_fixed[i]:>10.1f} | {baselines['hand_coupled_heuristic'][i]:>12.1f} | {oracle[i]:>6}")
    print()
    print(json.dumps({k: v for k, v in result.items() if not k.startswith("curve_")}, indent=2))


if __name__ == "__main__":
    main()
