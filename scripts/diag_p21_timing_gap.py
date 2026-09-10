#!/usr/bin/env python3
"""P21 DIAGNOSTIC (exploratory, not a gated claim).

P18 passed but left a documented gap: in the 110-140 deg separation band the learned
policy reaches 18 / 7.3 / 3 / 1 delivered while the dynamic-programming oracle reaches
42 / 34 / 20 / 9.  This script asks WHY, because the answer decides whether a mechanism
layer exists at all.

Structural fact that frames the whole diagnosis: with radar half-FOV 65 deg and link
half-angle 45 deg, a single nose can satisfy BOTH duties simultaneously only when
    separation <= 65 + 45 = 110 deg.
Above 110 deg the agent must time-share: refresh the cache by looking at the target,
then swing the nose onto the relay and deliver before the cache goes stale.  The swing
costs (separation - 110)/5 steps at a 5 deg/step turn limit, against a TTL of 8 steps.

Hypotheses discriminated here:
  H1 CAPACITY / OPTIMISATION - a wider net or a longer run closes the band, so the gap
     is just under-training and there is no mechanism story.
  H2 EXPLORATION / DISCOVERY - the policy never discovers the time-sharing pattern at
     high separation (it latches onto one duty), so the fix is a curriculum, not a net.
  H3 TIMING PRECISION - the policy finds the pattern but mistimes the swing.

Behavioural fingerprint per separation classifies the failure:
  BOTH      fresh cache and link up on the same step
  TGT_ONLY  looking at the target, link down
  LNK_ONLY  link up, cache stale
  NEITHER   neither duty served
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
from p18_train_coupled_policy import (  # noqa: E402
    ActorCritic,
    force_geometry,
    oracle_dp,
    wrap,
)

FOCUS_BAND = [110, 120, 130, 140]


# --------------------------------------------------------------- training


def train_variant(cfg, seed, device, hidden=64, stages=((10.0, 180.0, 600),)):
    """Train with an optional staged separation curriculum.

    stages is a sequence of (sep_min, sep_max, updates); environments are rebuilt
    whenever the separation range changes, so a curriculum is easy-then-hard.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)
    t = dict(cfg["training"])
    t["hidden_dim"] = hidden
    net = None
    opt = None
    obs = None
    for stage_idx, (sep_lo, sep_hi, updates) in enumerate(stages):
        envs = [
            AttitudeCoupledRelayEnv(
                AttitudeCoupledRelayConfig(
                    seed=seed * 1000 + i,
                    separation_min_deg=sep_lo,
                    separation_max_deg=sep_hi,
                )
            )
            for i in range(t["parallel_envs"])
        ]
        obs = np.stack([e.reset()[0] for e in envs])
        if net is None:
            net = ActorCritic(envs[0].obs_dim, envs[0].action_dim, hidden).to(device)
            opt = optim.Adam(net.parameters(), lr=t["lr"], eps=1e-5)
        if stage_idx > 0:
            # fresh optimiser state keeps the second stage from inheriting stale moments
            opt = optim.Adam(net.parameters(), lr=t["lr"], eps=1e-5)
        t["updates"] = updates
        _run_stage(cfg, net, opt, envs, obs, t, device)
    net.eval()
    return net


def _run_stage(cfg, net, opt, envs, obs, t, device):
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
        rew, dones, vals = np.asarray(r_buf), np.asarray(d_buf), np.asarray(v_buf)
        adv = np.zeros_like(rew)
        last = np.zeros(n_envs, dtype=np.float32)
        for s in reversed(range(horizon)):
            nxt = last_v if s == horizon - 1 else vals[s + 1]
            nonterm = 1.0 - dones[s]
            last = rew[s] + t["gamma"] * nxt * nonterm - vals[s] + t["gamma"] * t["gae_lambda"] * nonterm * last
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
    return net


def evaluate_band(net, device, separations):
    env = AttitudeCoupledRelayEnv(AttitudeCoupledRelayConfig(seed=12345))
    out = {}
    for sep in separations:
        obs = force_geometry(env, sep)
        while not env.done:
            with torch.no_grad():
                logits, _ = net(torch.as_tensor(obs[None, :], dtype=torch.float32, device=device))
            obs, _, _, _, _, _ = env.step(int(torch.argmax(logits, dim=-1).item()))
        out[sep] = float(env.delivered)
    return out


# --------------------------------------------------------------- oracle trace


def oracle_trace(sep_deg: float, cfg: dict, n_head: int = 72):
    """Time-indexed backward DP then a greedy forward rollout.

    The forward pass must consult V_k, the value with k steps REMAINING.  Using the
    single full-horizon table at every step is wrong and silently produces a
    non-optimal trace (this was a bug in the first version of this diagnostic, of the
    same family as the P18 section 5.1 oracle bug).
    """
    e = cfg["environment"]
    grid = np.linspace(-math.pi, math.pi, n_head, endpoint=False)
    half_fov = math.radians(e["radar_half_fov_deg"])
    half_link = math.radians(e["link_half_angle_deg"])
    ttl, horizon = e["cache_ttl_steps"], e["horizon_steps"]
    tb, rb = 0.0, math.radians(sep_deg)
    det = np.abs(((grid - tb + math.pi) % (2 * math.pi)) - math.pi) <= half_fov
    lnk = np.abs(((grid - rb + math.pi) % (2 * math.pi)) - math.pi) <= half_link
    ages = ttl + 2

    vs = [np.zeros((n_head, ages))]  # vs[k] = optimal value with k steps remaining
    for _ in range(horizon):
        prev = vs[-1]
        nv = np.zeros((n_head, ages))
        for h in range(n_head):
            for a in range(ages):
                best = -1.0
                for dh in (-1, 0, 1):
                    h2 = (h + dh) % n_head
                    a2 = 0 if det[h2] else min(a + 1, ttl + 1)
                    r = 1.0 if (a2 <= ttl and lnk[h2]) else 0.0
                    best = max(best, r + prev[h2, a2])
                nv[h, a] = best
        vs.append(nv)

    h = int(np.argmin(np.abs(((grid - 0.0 + math.pi) % (2 * math.pi)) - math.pi)))
    age = ttl + 1
    rows = []
    for t in range(horizon):
        remaining = horizon - t - 1
        best_dh, best_cand = 0, -1.0
        for dh in (-1, 0, 1):
            h2 = (h + dh) % n_head
            a2 = 0 if det[h2] else min(age + 1, ttl + 1)
            r = 1.0 if (a2 <= ttl and lnk[h2]) else 0.0
            cand = r + vs[remaining][h2, a2]
            if cand > best_cand:
                best_cand, best_dh = cand, dh
        h = (h + best_dh) % n_head
        age = 0 if det[h] else min(age + 1, ttl + 1)
        rows.append((t, float(math.degrees(grid[h])), int(age), bool(det[h]), bool(lnk[h]),
                     bool(age <= ttl and lnk[h])))
    return rows


def classify(rows):
    """Turn a per-step trace into a fingerprint of which duty was served."""
    counts = {"BOTH": 0, "TGT_ONLY": 0, "LNK_ONLY": 0, "NEITHER": 0}
    for _, _, age, det, lnk, delivered in rows:
        fresh = age <= 8
        if det and lnk:
            counts["BOTH"] += 1
        elif det:
            counts["TGT_ONLY"] += 1
        elif lnk:
            counts["LNK_ONLY"] += 1
        else:
            counts["NEITHER"] += 1
    return counts


def learned_trace(net, sep_deg, device):
    env = AttitudeCoupledRelayEnv(AttitudeCoupledRelayConfig(seed=12345))
    obs = force_geometry(env, sep_deg)
    rows = []
    while not env.done:
        with torch.no_grad():
            logits, _ = net(torch.as_tensor(obs[None, :], dtype=torch.float32, device=device))
        a = int(torch.argmax(logits, dim=-1).item())
        t = env.step_count
        obs, _, _, _, _, _ = env.step(a)
        det = abs(wrap(env.target_bearing - env.heading)) <= env.half_fov
        lnk = abs(wrap(env.relay_bearing - env.heading)) <= env.half_link
        rows.append((t, float(math.degrees(env.heading)), int(env.cache_age), bool(det), bool(lnk),
                     bool(env.cache_age <= env.ttl and lnk)))
    return rows


def swing_cost_steps(sep_deg: float, cfg: dict) -> int:
    """Steps needed to travel from the target-visible edge to the relay-visible edge."""
    slack = cfg["environment"]["radar_half_fov_deg"] + cfg["environment"]["link_half_angle_deg"]
    gap = max(0.0, sep_deg - slack)
    return int(math.ceil(gap / cfg["environment"]["turn_limit_deg_per_step"]))


# --------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--seeds", type=int, default=2)
    args = ap.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    seeds = cfg["training"]["seeds"][: args.seeds]
    print(f"device={device} seeds={seeds}", flush=True)

    # --- structural budget table: how many steps a swing costs vs the TTL
    budget = {s: {"swing_steps": swing_cost_steps(s, cfg), "ttl": cfg["environment"]["cache_ttl_steps"]}
              for s in FOCUS_BAND}
    for s, v in budget.items():
        v["feasible_swing"] = v["swing_steps"] <= v["ttl"]

    variants = {
        # H1 capacity / optimisation
        "base_h64_u600": dict(hidden=64, stages=((10.0, 180.0, 600),)),
        "wide_h256_u600": dict(hidden=256, stages=((10.0, 180.0, 600),)),
        "long_h64_u2400": dict(hidden=64, stages=((10.0, 180.0, 2400),)),
        # H2 exploration / discovery
        "easy_only": dict(hidden=64, stages=((10.0, 110.0, 600),)),
        "curriculum": dict(hidden=64, stages=((10.0, 110.0, 300), (10.0, 180.0, 600))),
    }

    results = {}
    for name, kw in variants.items():
        per_seed = []
        for seed in seeds:
            net = train_variant(cfg, seed, device, **kw)
            per_seed.append(evaluate_band(net, device, FOCUS_BAND))
            print(f"{name} seed {seed}: band={per_seed[-1]}", flush=True)
        band = {s: float(np.mean([r[s] for r in per_seed])) for s in FOCUS_BAND}
        results[name] = {"band": band, "band_mean": float(np.mean(list(band.values())))}
        if name == "base_h64_u600":
            results[name]["traces"] = {
                str(s): {
                    "learned": classify(learned_trace(net, s, device)),
                    "oracle": classify(oracle_trace(s, cfg)),
                    "oracle_delivered": int(sum(r[5] for r in oracle_trace(s, cfg))),
                }
                for s in FOCUS_BAND
            }
        print(f"{name}: band_mean={results[name]['band_mean']:.2f}", flush=True)

    oracle_band = {s: oracle_dp(s, cfg) for s in FOCUS_BAND}
    out = {
        "diagnostic": "P21_TIMING_GAP",
        "status": "EXPLORATORY_NOT_A_GATED_CLAIM",
        "device": str(device),
        "focus_band_deg": FOCUS_BAND,
        "structural_budget": budget,
        "oracle_band": oracle_band,
        "oracle_band_mean": float(np.mean(list(oracle_band.values()))),
        "variants": results,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "P21_DIAG_RESULT.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print("\n=== structural budget ===")
    for s, v in budget.items():
        print(f"  sep {s}: swing {v['swing_steps']} steps vs TTL {v['ttl']} -> feasible_swing={v['feasible_swing']}")
    print("\n=== band (delivered) ===")
    print("variant            " + "".join(f"{s:>8}" for s in FOCUS_BAND) + "     mean")
    print("oracle             " + "".join(f"{oracle_band[s]:>8}" for s in FOCUS_BAND)
          + f"{np.mean(list(oracle_band.values())):>9.2f}")
    for name, r in results.items():
        print(f"{name:<18}" + "".join(f"{r['band'][s]:>8.1f}" for s in FOCUS_BAND) + f"{r['band_mean']:>9.2f}")
    print("\n=== base duty fingerprint (learned vs oracle) ===")
    for s in FOCUS_BAND:
        t = results["base_h64_u600"].get("traces", {}).get(str(s))
        if t:
            print(f"  sep {s}: learned {t['learned']}  |  oracle {t['oracle']} (delivered {t['oracle_delivered']})")


if __name__ == "__main__":
    main()
