#!/usr/bin/env python3
"""P19: does the attitude coupling stay load bearing when it becomes a team problem?

Trains a parameter-sharing PPO on the 3-agent relay chain (S->R->K) under attitude
coupling, partial observability and randomized geometry, then tests the three gates
frozen in configs/p19_team_attitude_coupled_20260910.json:

  G1 learned >= 1.20 x best scripted synchronized schedule
  G2 learned-with-clock >= 1.20 x learned-without-clock  (is synchronized timing essential?)
  G3 held-out geometry >= 0.80 x train-range geometry
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
from envs.attitude_coupled_team_env import (  # noqa: E402
    AttitudeCoupledTeamEnv,
    TeamCoupledConfig,
    TURN_ACTIONS,
)

N_AGENTS = 3

FROZEN_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "p19_team_attitude_coupled_20260910.json"

_ENV_KEYS = (
    "chain_spacing",
    "radar_half_fov_deg",
    "link_half_angle_deg",
    "turn_limit_deg_per_step",
    "cache_ttl_steps",
    "horizon_steps",
    # P20 motion block.  These must be bound from the config or the moving-task
    # round would silently execute the stationary P19 physics instead.
    "agent_speed",
    "target_speed",
    "link_range",
    "chain_bend_min_deg",
    "chain_bend_max_deg",
)


def env_kwargs(cfg: dict | None = None) -> dict:
    """Bind the frozen JSON environment block to the env dataclass.

    Without this the run silently falls back to dataclass defaults, so editing the
    frozen config would have no effect and a reviewer could not tell which numbers
    were actually executed.  The V2 round happened to match the defaults, so this
    is a provenance fix, not a behaviour change for that round.
    """
    if cfg is None:
        cfg = json.loads(FROZEN_CONFIG.read_text(encoding="utf-8"))
    e = cfg["environment"]
    kw = {k: e[k] for k in _ENV_KEYS if k in e}
    bend = e.get("chain_bend_deg")
    if bend is not None:
        kw["chain_bend_min_deg"] = float(bend[0])
        kw["chain_bend_max_deg"] = float(bend[1])
    return kw


def wrap(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


class TeamActorCritic(nn.Module):
    """Parameter sharing across agents; role enters through a one-hot input."""

    def __init__(self, obs_dim: int, action_dim: int, hidden: int):
        super().__init__()
        self.actor = nn.Sequential(
            nn.Linear(obs_dim + 3, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, action_dim),
        )
        self.critic = nn.Sequential(
            nn.Linear(obs_dim + 3, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1),
        )

    def forward(self, obs, role_onehot):
        x = torch.cat([obs, role_onehot], dim=-1)
        return self.actor(x), self.critic(x).squeeze(-1)


def role_onehot(device):
    return torch.eye(3, device=device).repeat(1, 1)


def flatten_obs(obs):
    """(n_agents, obs_dim) -> (n_agents*(obs_dim+3),) concatenated with role one-hot."""
    obs = np.asarray(obs)
    n, d = obs.shape
    roles = np.eye(3)
    return np.concatenate([obs, roles], axis=1).reshape(-1).astype(np.float32)


def act_all(net, obs, device, greedy=False):
    obs = np.asarray(obs)
    lead = obs.shape[:-1]
    flat = obs.reshape(-1, obs.shape[-1])
    n = flat.shape[0] // N_AGENTS
    obs_t = torch.as_tensor(flat, dtype=torch.float32, device=device)
    roles = torch.eye(3, device=device).repeat(n, 1)
    logits, value = net(obs_t, roles)
    dist = Categorical(logits=logits)
    a = torch.argmax(logits, dim=-1) if greedy else dist.sample()
    return a.reshape(lead), dist.log_prob(a).reshape(lead), value.reshape(lead)


def train_arm(cfg: dict, seed: int, include_clock: bool, device):
    torch.manual_seed(seed)
    np.random.seed(seed)
    t = cfg["training"]
    envs = [
        AttitudeCoupledTeamEnv(
            TeamCoupledConfig(seed=seed * 1000 + i, include_clock=include_clock, **env_kwargs(cfg))
        )
        for i in range(t["parallel_envs"])
    ]
    obs = np.stack([e.reset()[0] for e in envs])
    net = TeamActorCritic(6, 3, t["hidden_dim"]).to(device)
    opt = optim.Adam(net.parameters(), lr=t["lr"], eps=1e-5)
    n_envs, horizon = t["parallel_envs"], t["rollout_steps"]

    for _ in range(t["updates"]):
        o_buf, a_buf, lp_buf, r_buf, d_buf, v_buf = [], [], [], [], [], []
        for _ in range(horizon):
            with torch.no_grad():
                act, lp, val = act_all(net, obs, device)
            o_buf.append(obs.copy())
            a_buf.append(act.cpu().numpy())
            lp_buf.append(lp.cpu().numpy())
            v_buf.append(val.squeeze(-1).cpu().numpy())
            r, d, nobs = [], [], []
            for i, env in enumerate(envs):
                ob, _, _, rew, dn, _ = env.step(act[i].cpu().numpy())
                if dn[0] > 0.5:
                    ob = env.reset()[0]
                nobs.append(ob)
                r.append(rew[0])
                d.append(dn[0])
            r_buf.append(np.asarray(r, dtype=np.float32))
            d_buf.append(np.asarray(d, dtype=np.float32))
            obs = np.stack(nobs)

        with torch.no_grad():
            obs_t = torch.as_tensor(obs.reshape(-1, 6), dtype=torch.float32, device=device)
            roles = torch.eye(3, device=device).repeat(n_envs, 1)
            _, last_v = net(obs_t, roles)
            last_v = last_v.reshape(n_envs, N_AGENTS).cpu().numpy()
        rew = np.asarray(r_buf)[:, :, None]      # (H, E, 1) shared team reward
        dones = np.asarray(d_buf)[:, :, None]    # (H, E, 1)
        vals = np.asarray(v_buf)                 # (H, E, 3)
        adv = np.zeros_like(vals)
        last = np.zeros((n_envs, N_AGENTS), dtype=np.float32)
        for s in reversed(range(horizon)):
            nxt = last_v if s == horizon - 1 else vals[s + 1]
            nonterm = 1.0 - dones[s]
            delta = rew[s] + t["gamma"] * nxt * nonterm - vals[s]
            last = delta + t["gamma"] * t["gae_lambda"] * nonterm * last
            adv[s] = last
        ret = adv + vals

        flat_obs = np.asarray(o_buf).reshape(-1, 6)
        o = torch.as_tensor(flat_obs, dtype=torch.float32, device=device)
        roles = torch.eye(3, device=device).repeat(flat_obs.shape[0] // 3, 1)
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
                logits, value = net(o[mb], roles[mb])
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


# ------------------------------------------------------------------ evaluation


def eval_learned(net, geometries, include_clock, device, cfg: dict | None = None):
    env = AttitudeCoupledTeamEnv(
        TeamCoupledConfig(seed=0, include_clock=include_clock, **env_kwargs(cfg))
    )
    scores = []
    for seed in geometries:
        env.seed(seed)
        obs, _, _ = env.reset()
        while not env.done:
            with torch.no_grad():
                act, _, _ = act_all(net, obs, device, greedy=True)
            obs, _, _, _, _, _ = env.step(act.cpu().numpy())
        scores.append(float(env.score))
    return scores


def eval_schedule(geometries, period, duty, phases, include_clock=True, cfg: dict | None = None):
    env = AttitudeCoupledTeamEnv(
        TeamCoupledConfig(seed=0, include_clock=include_clock, **env_kwargs(cfg))
    )
    scores = []
    for seed in geometries:
        env.seed(seed)
        env.reset()
        while not env.done:
            duties = env._duty_bearings()
            acts = []
            for i in range(N_AGENTS):
                want_a = ((env.step_count + phases[i]) % period) < duty
                desired = duties[i][0] if want_a else duties[i][1]
                err = wrap(desired - env.headings[i])
                if err > env.turn * 0.5:
                    acts.append(2)      # increase heading
                elif err < -env.turn * 0.5:
                    acts.append(0)      # decrease heading
                else:
                    acts.append(1)
            env.step(np.asarray(acts))
        scores.append(float(env.score))
    return scores


def search_schedule(geometries, rng, trials=80, cfg: dict | None = None):
    best = {"mean": -1.0, "period": 4, "duty": 2, "phases": (0, 0, 0)}
    for _ in range(trials):
        period = int(rng.integers(4, 21))
        duty = int(rng.integers(1, period))
        phases = tuple(int(rng.integers(0, period)) for _ in range(N_AGENTS))
        scores = eval_schedule(geometries, period, duty, phases, cfg=cfg)
        mean = float(np.mean(scores))
        if mean > best["mean"]:
            best = {"mean": mean, "period": period, "duty": duty, "phases": phases}
    return best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    accepted = ("P19-TEAM-ATTITUDE-COUPLED-V2", "P20-MOVING-TEAM-ATTITUDE-COUPLED-V1")
    if cfg["protocol"] not in accepted:
        raise ValueError("protocol mismatch")
    tag = "P20" if cfg["protocol"].startswith("P20") else "P19"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_geo = list(range(31000, 31100))
    hold_geo = list(range(32000, 32100))
    print(f"device={device}")
    print("env=" + json.dumps(env_kwargs(cfg), sort_keys=True), flush=True)

    with_clock, without_clock = [], []
    for seed in cfg["training"]["seeds"]:
        net = train_arm(cfg, seed, True, device)
        s = eval_learned(net, train_geo + hold_geo, True, device, cfg=cfg)
        with_clock.append(s)
        print(f"[clock ] seed {seed}: train={np.mean(s[:100]):.2f} hold={np.mean(s[100:]):.2f}", flush=True)
        net2 = train_arm(cfg, seed, False, device)
        s2 = eval_learned(net2, train_geo + hold_geo, False, device, cfg=cfg)
        without_clock.append(s2)
        print(f"[noclok] seed {seed}: train={np.mean(s2[:100]):.2f} hold={np.mean(s2[100:]):.2f}")

    wc = np.mean(np.stack(with_clock), axis=0)
    nc = np.mean(np.stack(without_clock), axis=0)

    rng = np.random.default_rng(7)
    base = eval_schedule(train_geo, 8, 3, (0, 0, 0), cfg=cfg)
    sch = search_schedule(train_geo, rng, trials=120, cfg=cfg)
    scripted_mean = sch["mean"]

    learned_train = float(np.mean(wc[:100]))
    learned_hold = float(np.mean(wc[100:]))
    learned_mean = float(np.mean(wc))
    noclk_mean = float(np.mean(nc))

    not_vacuous = bool(learned_mean > 0.0 and scripted_mean > 0.0)
    checks = {
        "G0_not_vacuous": not_vacuous,
        "G1_beats_scripted_schedule_by_20pct": learned_mean >= 1.20 * scripted_mean,
        "G2_clock_is_load_bearing": learned_mean >= 1.20 * noclk_mean,
        "G3_holds_out": learned_hold >= 0.80 * learned_train,
    }
    if not not_vacuous:
        verdict = f"{tag}_INFEASIBLE_OR_VACUOUS"
    elif all(checks.values()):
        verdict = f"{tag}_PASS"
    else:
        verdict = f"{tag}_FAIL"
    result = {
        "protocol": cfg["protocol"],
        "verdict": verdict,
        "gates_evaluated": bool(not_vacuous),
        "device": str(device),
        "learned_mean": learned_mean,
        "learned_train_mean": learned_train,
        "learned_holdout_mean": learned_hold,
        "no_clock_mean": noclk_mean,
        "scripted_best": sch,
        "scripted_baseline_default_mean": float(np.mean(base)),
        "checks": checks,
        "environment_steps": (
            cfg["training"]["updates"] * cfg["training"]["parallel_envs"]
            * cfg["training"]["rollout_steps"] * len(cfg["training"]["seeds"]) * 2
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "P19_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
