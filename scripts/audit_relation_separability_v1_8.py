"""Low-cost, method-independent relation separability audit for v1.8."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import (  # noqa: E402
    RELATION_COMMUNICATION,
    RELATION_PERCEPTION,
    RELATION_TASK_SUPPORT,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
)


PAIRS = ((RELATION_PERCEPTION, RELATION_COMMUNICATION),
         (RELATION_COMMUNICATION, RELATION_TASK_SUPPORT),
         (RELATION_PERCEPTION, RELATION_TASK_SUPPORT))
NAMES = {RELATION_PERCEPTION: "perception", RELATION_COMMUNICATION: "communication",
         RELATION_TASK_SUPPORT: "task_support"}


def collect(name: str, cfg: UAVIntercept3DConfig, seeds: list[int], horizon: int = 80):
    rows = []
    for seed in seeds:
        env_cfg = UAVIntercept3DConfig(**{**cfg.__dict__, "seed": seed})
        env = UAVIntercept3DEnv(env_cfg)
        _, _, graph = env.reset()
        for t in range(horizon):
            rel = graph["relation_adj"].astype(np.int8)
            rows.append((name, seed, t, rel))
            actions = np.asarray([(seed + 3 * t + i) % env.action_dim for i in range(env.num_agents)])
            _, _, graph, _, dones, _ = env.step(actions)
            if bool(np.asarray(dones).any()):
                break
    return rows


def summarize(rows):
    out = {"n_steps": len(rows), "relations": {}, "pairs": {}, "task_vs_comm": {}}
    for rid, name in NAMES.items():
        arr = np.concatenate([x[3][rid].reshape(-1) for x in rows])
        out["relations"][name] = {"edge_count_mean": float(arr.sum() / len(rows)),
                                   "active_rate": float(arr.mean())}
    for a, b in PAIRS:
        eq = []; jacc = []; overlap = []; disagree = []
        for _, _, _, rel in rows:
            x, y = rel[a].astype(bool), rel[b].astype(bool)
            inter = np.logical_and(x, y).sum(); union = np.logical_or(x, y).sum()
            eq.append(float(np.array_equal(x, y)))
            overlap.append(float(inter)); jacc.append(float(inter / union) if union else 1.0)
            disagree.append(float(np.not_equal(x, y).mean()))
        key = f"{NAMES[a]}_vs_{NAMES[b]}"
        out["pairs"][key] = {"time_identical_rate": float(np.mean(eq)),
                              "mean_overlap": float(np.mean(overlap)),
                              "mean_jaccard": float(np.mean(jacc)),
                              "mean_disagreement_rate": float(np.mean(disagree))}
    comm_edges = task_edges = task_without_comm = comm_without_task = 0
    for _, _, _, rel in rows:
        c = rel[RELATION_COMMUNICATION].astype(bool)
        s = rel[RELATION_TASK_SUPPORT].astype(bool)
        comm_edges += int(c.sum()); task_edges += int(s.sum())
        task_without_comm += int(np.logical_and(s, ~c).sum())
        comm_without_task += int(np.logical_and(c, ~s).sum())
    out["task_vs_comm"] = {
        "communication_edges": comm_edges,
        "task_support_edges": task_edges,
        "task_without_communication": task_without_comm,
        "communication_without_task_support": comm_without_task,
        "task_support_over_communication_ratio": float(task_edges / comm_edges) if comm_edges else 0.0,
    }
    return out


def main():
    base = UAVIntercept3DConfig(
        communication_dropout_prob=0.0, message_delay_steps=0,
        failed_blue_agent=-1, node_failure_start_step=0, node_failure_duration_steps=0,
    )
    stress = UAVIntercept3DConfig(
        communication_dropout_prob=0.35, message_delay_steps=2,
        failed_blue_agent=1, node_failure_start_step=20, node_failure_duration_steps=8,
    )
    for name, cfg in (("nominal", base), ("early_nominal_anchor", base), ("relay_delay_loss", stress)):
        seeds = [7, 19, 31] if name != "early_nominal_anchor" else [101, 203, 307]
        print(name, summarize(collect(name, cfg, seeds)))


if __name__ == "__main__":
    main()
