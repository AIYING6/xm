from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from baselines.rule_policy import greedy_intercept_policy
from envs.uav_pursuit_env import UAVPursuitConfig, UAVPursuitEnv


def run_episode(seed: int = 0):
    env = UAVPursuitEnv(UAVPursuitConfig(seed=seed, target_policy="nearest_escape"))
    obs, share_obs, graph_obs = env.reset()
    info = {}
    while True:
        actions = greedy_intercept_policy(env)
        obs, share_obs, graph_obs, rewards, dones, info = env.step(actions)
        if np.all(dones):
            break
    return env, info


def plot_episode(env: UAVPursuitEnv, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if plt is None:
        csv_path = out_path.with_suffix(".csv")
        save_episode_csv(env, csv_path)
        return

    p_hist = np.asarray(env.history["p_pos"])
    t_hist = np.asarray(env.history["t_pos"])
    fig, ax = plt.subplots(figsize=(6, 6))
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:purple", "tab:brown"]

    for i in range(env.config.num_pursuers):
        ax.plot(p_hist[:, i, 0], p_hist[:, i, 1], color=colors[i % len(colors)], label=f"UAV {i}")
        ax.scatter(p_hist[0, i, 0], p_hist[0, i, 1], color=colors[i % len(colors)], marker="o", s=30)
        ax.scatter(p_hist[-1, i, 0], p_hist[-1, i, 1], color=colors[i % len(colors)], marker="x", s=50)

    for j in range(env.config.num_targets):
        ax.plot(t_hist[:, j, 0], t_hist[:, j, 1], color="tab:red", linestyle="--", label=f"Target {j}")
        ax.scatter(t_hist[0, j, 0], t_hist[0, j, 1], color="tab:red", marker="o", s=30)
        ax.scatter(t_hist[-1, j, 0], t_hist[-1, j, 1], color="tab:red", marker="x", s=50)

    half = env.config.world_size / 2
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(
        f"Rule policy | success={int(env.success)} collision={int(env.collision)} steps={env.step_count}"
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def save_episode_csv(env: UAVPursuitEnv, out_path: Path) -> None:
    p_hist = np.asarray(env.history["p_pos"])
    t_hist = np.asarray(env.history["t_pos"])
    rows = []
    for t in range(p_hist.shape[0]):
        vals = [str(t)]
        for i in range(env.config.num_pursuers):
            vals.extend([f"{p_hist[t, i, 0]:.6f}", f"{p_hist[t, i, 1]:.6f}"])
        for j in range(env.config.num_targets):
            vals.extend([f"{t_hist[t, j, 0]:.6f}", f"{t_hist[t, j, 1]:.6f}"])
        rows.append(",".join(vals))
    header = ["step"]
    for i in range(env.config.num_pursuers):
        header.extend([f"uav{i}_x", f"uav{i}_y"])
    for j in range(env.config.num_targets):
        header.extend([f"target{j}_x", f"target{j}_y"])
    out_path.write_text(",".join(header) + "\n" + "\n".join(rows), encoding="utf-8")


def main():
    env, info = run_episode(seed=0)
    out_path = ROOT / "results" / "rule_episode.png"
    plot_episode(env, out_path)
    print(
        {
            "success": env.success,
            "collision": env.collision,
            "steps": env.step_count,
            "mean_distance": info.get("mean_distance"),
            "output": str(out_path if plt is not None else out_path.with_suffix(".csv")),
        }
    )


if __name__ == "__main__":
    main()
