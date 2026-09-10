#!/usr/bin/env python3
"""P22: are goal-driven, non-interruptible swing options the mechanism the P21 diagnosis asked for?

P21 showed the 110-140 deg gap is neither capacity nor exploration.  The learned
primitive policy already alternates with roughly the oracle's duty split, but it
reaches the delivery pose with a mean cache age of 7.8-8.6 against a TTL of 8, while
the oracle arrives with 4.4-6.0.  The information needed is already in the
observation; what is missing is temporal abstraction, because "start the swing" is not
a decision in a +/-5 deg per-step action space, it is six consecutive micro-decisions.

P22 removes the primitive action space and replaces it with two committed maneuvers:

    SERVE_TARGET : turn at the full turn limit toward the target, terminate once the
                   target is inside the radar half-FOV
    SERVE_RELAY  : turn at the full turn limit toward the relay, terminate once the
                   relay is inside the link half-angle

The policy is queried only at decision epochs, so starting a swing is one decision.
Neither option can be abandoned mid-swing; that is the deliberate design choice.

Gates were frozen in configs/p22_swing_option_20260911.json BEFORE running.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from envs.attitude_coupled_relay_env import (  # noqa: E402
    AttitudeCoupledRelayConfig,
    AttitudeCoupledRelayEnv,
)
from p18_train_coupled_policy import ActorCritic, force_geometry, oracle_dp, wrap  # noqa: E402
from diag_p21_timing_gap import train_variant  # noqa: E402

N_OPTIONS = 2  # SERVE_TARGET, SERVE_RELAY


# ------------------------------------------------------------- option controller


def primitive_action(env, option: int) -> int:
    """Closed-loop primitive that drives the nose toward the option's goal."""
    desired = env.target_bearing if option == 0 else env.relay_bearing
    err = wrap(desired - env.heading)
    if err > env.turn * 0.5:
        return 2      # increase heading
    if err < -env.turn * 0.5:
        return 0      # decrease heading
    return 1


def goal_met(env, option: int) -> bool:
    if option == 0:
        return abs(wrap(env.target_bearing - env.heading)) <= env.half_fov
    return abs(wrap(env.relay_bearing - env.heading)) <= env.half_link


# ------------------------------------------------------------- option training


def train_options(cfg, seed, device):
    t = cfg["training"]
    torch.manual_seed(seed)
    np.random.seed(seed)
    n_envs = t["parallel_envs"]
    maxdur = t["max_option_steps"]
    envs = [
        AttitudeCoupledRelayEnv(AttitudeCoupledRelayConfig(seed=seed * 1000 + i))
        for i in range(n_envs)
    ]
    obs = [e.reset()[0] for e in envs]
    net = ActorCritic(envs[0].obs_dim, N_OPTIONS, t["hidden_dim"]).to(device)
    opt = optim.Adam(net.parameters(), lr=t["lr"], eps=1e-5)
    gamma, lam = t["gamma"], t["gae_lambda"]
    total_env_steps = 0

    for _ in range(t["updates"]):
        seqs = [[] for _ in range(n_envs)]
        used = [0] * n_envs
        for i, env in enumerate(envs):
            while used[i] < t["rollout_steps"]:
                obs_dec = obs[i]
                with torch.no_grad():
                    logits, val = net(torch.as_tensor(obs_dec[None, :], dtype=torch.float32, device=device))
                    dist = Categorical(logits=logits)
                    o = dist.sample()
                    lp = dist.log_prob(o)
                reward_sum, dur, terminal = 0.0, 0, False
                while True:
                    a = primitive_action(env, int(o.item()))
                    nobs, _, _, rew, dn, _ = env.step(a)
                    reward_sum += float(rew[0])
                    dur += 1
                    used[i] += 1
                    total_env_steps += 1
                    if goal_met(env, int(o.item())) or dur >= maxdur or dn[0] > 0.5:
                        break
                if dn[0] > 0.5:
                    terminal = True
                    nobs = env.reset()[0]
                seqs[i].append(
                    {
                        "obs": obs_dec,
                        "opt": int(o.item()),
                        "lp": float(lp.item()),
                        "val": float(val.item()),
                        "R": reward_sum,
                        "d": dur,
                        "next": nobs,
                        "terminal": terminal,
                    }
                )
                obs[i] = nobs

        flat, adv_all, ret_all = [], [], []
        for i in range(n_envs):
            seq = seqs[i]
            if not seq:
                continue
            with torch.no_grad():
                _, boot = net(torch.as_tensor(seq[-1]["next"][None, :], dtype=torch.float32, device=device))
                boot = float(boot.item())
            vals = [s["val"] for s in seq]
            adv = [0.0] * len(seq)
            running = 0.0
            for k in reversed(range(len(seq))):
                nxt_v = 0.0 if seq[k]["terminal"] else (boot if k == len(seq) - 1 else vals[k + 1])
                disc = gamma ** seq[k]["d"]
                delta = seq[k]["R"] + disc * nxt_v - vals[k]
                nonterm = 0.0 if seq[k]["terminal"] else 1.0
                running = delta + disc * lam * nonterm * running
                adv[k] = running
            for k, s in enumerate(seq):
                flat.append(s)
                adv_all.append(adv[k])
                ret_all.append(adv[k] + s["val"])

        o_t = torch.as_tensor(np.stack([s["obs"] for s in flat]), dtype=torch.float32, device=device)
        a_t = torch.as_tensor([s["opt"] for s in flat], dtype=torch.long, device=device)
        lp_t = torch.as_tensor([s["lp"] for s in flat], dtype=torch.float32, device=device)
        adv_t = torch.as_tensor(adv_all, dtype=torch.float32, device=device)
        ret_t = torch.as_tensor(ret_all, dtype=torch.float32, device=device)
        adv_t = (adv_t - adv_t.mean()) / (adv_t.std() + 1e-8)

        idx = np.arange(o_t.shape[0])
        for _ in range(t["ppo_epochs"]):
            np.random.shuffle(idx)
            for start in range(0, len(idx), t["minibatch"]):
                mb = idx[start:start + t["minibatch"]]
                logits, value = net(o_t[mb])
                dist = Categorical(logits=logits)
                nlp = dist.log_prob(a_t[mb])
                ratio = (nlp - lp_t[mb]).exp()
                pg = -torch.min(
                    adv_t[mb] * ratio,
                    adv_t[mb] * torch.clamp(ratio, 1 - t["clip_coef"], 1 + t["clip_coef"]),
                ).mean()
                vl = 0.5 * (ret_t[mb] - value).pow(2).mean()
                ent = dist.entropy().mean()
                loss = pg + t["value_coef"] * vl - t["entropy_coef"] * ent
                opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(net.parameters(), 0.5)
                opt.step()

    net.eval()
    return net, total_env_steps


@torch.no_grad()
def evaluate_options(net, separations, device):
    env = AttitudeCoupledRelayEnv(AttitudeCoupledRelayConfig(seed=12345))
    out = []
    for sep in separations:
        obs = force_geometry(env, sep)
        while not env.done:
            logits, _ = net(torch.as_tensor(obs[None, :], dtype=torch.float32, device=device))
            o = int(torch.argmax(logits, dim=-1).item())
            dur = 0
            while not env.done:
                obs, _, _, _, _, _ = env.step(primitive_action(env, o))
                dur += 1
                if goal_met(env, o) or dur >= 15:
                    break
        out.append(float(env.delivered))
    return out


def evaluate_primitives(net, separations, device):
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    if cfg["protocol"] != "P22-SWING-OPTION-V1":
        raise ValueError("protocol mismatch")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t = cfg["training"]
    grid = list(range(0, 181, 10))
    band = cfg["evaluation"]["focus_band_deg"]
    easy = cfg["evaluation"]["easy_region_deg"]
    budget_target = t["updates"] * t["parallel_envs"] * t["rollout_steps"]
    print(f"device={device}  budget_target_env_steps={budget_target}", flush=True)

    opt_runs, opt_steps = [], []
    for seed in t["seeds"]:
        net, steps = train_options(cfg, seed, device)
        opt_steps.append(steps)
        opt_runs.append(evaluate_options(net, grid, device))
        print(f"[options] seed {seed}: env_steps={steps} grid_mean={np.mean(opt_runs[-1]):.2f}", flush=True)

    options_curve = np.mean(np.stack(opt_runs), axis=0)
    mean_opt_steps = int(np.mean(opt_steps))
    prim_updates = max(1, int(round(mean_opt_steps / (t["parallel_envs"] * t["rollout_steps"]))))

    prim_runs = []
    for seed in t["seeds"]:
        net = train_variant(cfg, seed, device, hidden=t["hidden_dim"],
                            stages=((10.0, 180.0, prim_updates),))
        prim_runs.append(evaluate_primitives(net, grid, device))
        print(f"[primitives] seed {seed}: updates={prim_updates} grid_mean={np.mean(prim_runs[-1]):.2f}", flush=True)
    prim_curve = np.mean(np.stack(prim_runs), axis=0)

    oracle_curve = [oracle_dp(s, cfg) for s in grid]

    def at(curve, seps):
        return float(np.mean([curve[grid.index(s)] for s in seps]))

    band_opt, band_prim, band_oracle = at(options_curve, band), at(prim_curve, band), at(oracle_curve, band)
    easy_opt, easy_prim = at(options_curve, easy), at(prim_curve, easy)
    all_opt, all_prim = float(np.mean(options_curve)), float(np.mean(prim_curve))

    not_vacuous = bool(band_opt > 0.0 and band_prim > 0.0)
    checks = {
        "G0_not_vacuous": not_vacuous,
        "G1_band_gain": band_opt >= 1.20 * band_prim,
        "G2_reaches_oracle": band_opt >= 0.80 * band_oracle,
        "G3_no_easy_region_regression": easy_opt >= 0.90 * easy_prim,
        "G4_whole_grid_no_regression": all_opt >= 0.90 * all_prim,
    }
    if not not_vacuous:
        verdict = "P22_INFEASIBLE_OR_VACUOUS"
    elif all(checks.values()):
        verdict = "P22_PASS"
    else:
        verdict = "P22_FAIL"

    result = {
        "protocol": cfg["protocol"],
        "verdict": verdict,
        "device": str(device),
        "provenance": {
            "budget_target_env_steps": budget_target,
            "options_env_steps_per_seed": opt_steps,
            "options_env_steps_mean": mean_opt_steps,
            "primitives_updates_used": prim_updates,
            "primitives_env_steps_equivalent": prim_updates * t["parallel_envs"] * t["rollout_steps"],
            "budget_deviation_pct": 100.0 * abs(mean_opt_steps - prim_updates * t["parallel_envs"] * t["rollout_steps"]) / budget_target,
        },
        "focus_band_deg": band,
        "band": {"options": band_opt, "primitives": band_prim, "oracle": band_oracle,
                 "ratio_options_over_primitives": band_opt / band_prim if band_prim else None},
        "easy_region": {"options": easy_opt, "primitives": easy_prim},
        "whole_grid": {"options": all_opt, "primitives": all_prim},
        "grid_deg": grid,
        "curve_options": list(map(float, options_curve)),
        "curve_primitives": list(map(float, prim_curve)),
        "curve_oracle": list(map(float, oracle_curve)),
        "checks": checks,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "P22_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print("\nsep | options | primitives | oracle")
    for i, s in enumerate(grid):
        print(f"{s:>3} | {options_curve[i]:>7.1f} | {prim_curve[i]:>10.1f} | {oracle_curve[i]:>6}")
    print()
    print(json.dumps({k: v for k, v in result.items() if not k.startswith("curve_")}, indent=2))


if __name__ == "__main__":
    main()
