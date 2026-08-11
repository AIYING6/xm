"""P2 audit on the actual MPE2 standard environments (no training)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Keep cac's compatible NumPy/SciPy first; the temporary MPE2 wheel is vendored
# on the data disk and appended only for this audit.
sys.path.append(str(Path(__file__).resolve().parents[1] / ".vendor"))

from mpe2 import simple_formation_v1, simple_spread_v3


def run(factory, seed, scope_agent=None, oracle=False, horizon=40):
    env = factory.parallel_env(N=3, continuous_actions=True)
    obs, _ = env.reset(seed=seed)
    agents = list(env.possible_agents)
    success = False
    for _ in range(horizon):
        acts = {}
        for idx, agent in enumerate(agents):
            x = np.asarray(obs[agent], dtype=np.float32).copy()
            # MPE observations begin with velocity/self-position, followed by
            # landmark-relative coordinates.  Masking those entries models a
            # sensing-scope perturbation without changing the physics.
            if scope_agent == idx and not oracle:
                x[4:min(10, len(x))] = 0.0
            rel = x[4:]
            rel = np.pad(rel[:6], (0, max(0, 6 - len(rel[:6]))))
            landmark_rel = rel.reshape(3, 2)
            u = np.clip(np.mean(landmark_rel, axis=0), -1.0, 1.0)
            action = np.zeros(5, dtype=np.float32)
            action[1:3] = (u + 1.0) / 2.0
            acts[agent] = action
        obs, rewards, terms, truncs, infos = env.step(acts)
        if all(bool(v) for v in terms.values()) or all(bool(v) for v in truncs.values()):
            success = True
            break
    env.close()
    return {"success": success, "steps": _ + 1, "mean_reward": float(np.mean(list(rewards.values())))}


def main():
    tasks = {"simple_spread": simple_spread_v3, "simple_formation": simple_formation_v1}
    seeds = [31001, 31002, 31003, 31004]
    rows = []
    for task, factory in tasks.items():
        for scope_agent in (None, 0, 1):
            for controller in ("oracle", "local_history"):
                trials = [run(factory, s, scope_agent, controller == "oracle") for s in seeds]
                rows.append({"task": task, "scope_agent": scope_agent, "controller": controller,
                             "success_rate": float(np.mean([x["success"] for x in trials])),
                             "mean_steps": float(np.mean([x["steps"] for x in trials])),
                             "mean_reward": float(np.mean([x["mean_reward"] for x in trials]))})
    out = {"protocol": "P2_MPE2_STANDARD_SCOPE_AUDIT", "training": False, "rows": rows}
    path = Path("results/p2_mpe2_scope_audit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
