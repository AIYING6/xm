"""Read-only P2 phenomenon audit.

This is deliberately a small MPE/Particle-style continuous cooperative
navigation audit.  It does not train a policy or implement a proposed method.
The audit compares scope-aware oracle, fixed/static, local-history and simple
mask controllers under paired hidden scope realizations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _step(pos, target, scope, controller, estimates, rng):
    n = len(pos)
    obs_target = target - pos
    if scope is not None:
        affected, modality = scope
        if modality == "sensing":
            obs_target[affected] = 0.0
        elif modality == "actuation":
            pass
    if controller == "oracle" and scope is not None:
        # Oracle knows which agent is affected and routes its action to the
        # least-affected teammate; this is only an upper-bound controller.
        affected, modality = scope
        if modality == "sensing":
            obs_target[affected] = target[affected] - pos[affected]
    # Every non-oracle controller acts on its own legal current estimate or
    # cached estimate; no controller receives scope truth or global target truth.
    if controller != "oracle":
        for i in range(n):
            if scope is None or scope[0] != i or scope[1] != "sensing":
                estimates[i] = obs_target[i].copy()
        obs_target = estimates.copy()
    actions = np.clip(obs_target, -0.12, 0.12)
    if controller == "static":
        # Static policy freezes the nominal estimate after the first observation.
        actions = np.clip(estimates, -0.12, 0.12)
    elif controller == "mask":
        if scope is not None and scope[1] == "sensing":
            actions[scope[0]] *= 0.0
    elif controller == "local_history":
        # A legal local-history controller holds the last target estimate when
        # current sensing is unavailable; no scope truth is supplied.
        actions = np.clip(estimates, -0.12, 0.12)
    if scope is not None and scope[1] == "actuation":
        actions[scope[0]] *= 0.0
    return actions


def run_episode(task, scope, controller, seed, horizon=80):
    rng = np.random.default_rng(seed)
    n = 3
    pos = rng.uniform(-1.0, 1.0, size=(n, 2))
    if task == "navigation":
        target = np.tile(np.array([0.0, 0.0]), (n, 1))
    else:
        target = np.array([[-0.35, 0.0], [0.35, 0.0], [0.0, 0.35]])
    estimates = np.zeros_like(pos)
    for t in range(horizon):
        actions = _step(pos, target, scope, controller, estimates, rng)
        pos = pos + actions
        if np.max(np.linalg.norm(pos - target, axis=1)) < 0.18:
            return {"success": True, "steps": t + 1}
    return {"success": False, "steps": horizon}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[24001, 24002, 24003, 24004])
    ap.add_argument("--out", type=Path, default=Path("results/p2_latent_scope_audit.json"))
    args = ap.parse_args()
    controllers = ["oracle", "static", "local_history", "mask"]
    scopes = {"nominal": None, "single_scope": (0, "sensing"),
              "switching_scope": (1, "sensing"), "correlated_scope": (0, "actuation")}
    rows = []
    for task in ("navigation", "formation"):
        for scope_name, scope in scopes.items():
            for controller in controllers:
                trials = [run_episode(task, scope, controller, seed) for seed in args.seeds]
                rows.append({"task": task, "scope": scope_name, "controller": controller,
                             "success_rate": float(np.mean([x["success"] for x in trials])),
                             "mean_steps": float(np.mean([x["steps"] for x in trials]))})
    out = {"protocol": "P2_PHENOMENON_AUDIT_PROTOCOL_FROZEN", "training": False,
           "rows": rows, "status": "AUDIT_DATA_GENERATED__INTERPRETATION_REQUIRED"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
