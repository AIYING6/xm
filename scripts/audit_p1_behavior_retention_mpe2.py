"""No-training P1 audit: does local policy improvement break competent behavior?"""
import json
from pathlib import Path
import sys
import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1] / ".vendor2"))
sys.path.append(str(Path(__file__).resolve().parents[1] / ".vendor"))
from mpe2 import simple_spread_v3, simple_formation_v1


def run(factory, seed, gain):
    env = factory.parallel_env(N=3, continuous_actions=True)
    obs, _ = env.reset(seed=seed)
    agents = list(env.possible_agents)
    total = 0.0
    for t in range(40):
        actions = {}
        for agent in agents:
            x = np.asarray(obs[agent], dtype=np.float32)
            rel = np.pad(x[4:10], (0, max(0, 6 - len(x[4:10]))))[:6].reshape(3, 2)
            u = np.clip(np.mean(rel, axis=0) * gain, -1.0, 1.0)
            a = np.zeros(5, dtype=np.float32)
            a[1:3] = (u + 1.0) / 2.0
            actions[agent] = a
        obs, rewards, terms, truncs, _ = env.step(actions)
        total += float(np.mean(list(rewards.values())))
        if all(terms.values()) or all(truncs.values()):
            break
    env.close()
    return {"return": total, "steps": t + 1, "completed": bool(all(terms.values()))}


def main():
    rows = []
    for task, factory in {"simple_spread": simple_spread_v3, "simple_formation": simple_formation_v1}.items():
        for seed in [41001, 41002, 41003, 41004]:
            base = run(factory, seed, 1.0)
            for gain in [1.15, 1.35, 1.60]:
                upd = run(factory, seed, gain)
                rows.append({"task": task, "seed": seed, "gain": gain,
                             "base": base, "updated": upd,
                             "return_delta": upd["return"] - base["return"],
                             "completion_delta": int(upd["completed"]) - int(base["completed"])})
    out = {"protocol": "P1_MPE2_BEHAVIOR_RETENTION_AUDIT", "training": False, "rows": rows}
    Path("results/p1_behavior_retention_mpe2.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
