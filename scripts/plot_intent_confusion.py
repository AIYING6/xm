from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs
from envs import NUM_INTENTS, UAVPursuitConfig, UAVPursuitEnv

INTENT_NAMES = ["straight", "escape_nearest", "turn_left", "turn_right", "unknown"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("results/ri_gmappo_edge_stage2_rand_seed1_20/actor_critic_latest.pt"))
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--communication-radius", type=float, default=8.0)
    parser.add_argument("--out-png", type=Path, default=Path("results/figures/intent_confusion_ri_staged.png"))
    parser.add_argument("--out-csv", type=Path, default=Path("results/intent_confusion_ri_staged.csv"))
    args = parser.parse_args()

    env0 = UAVPursuitEnv(
        UAVPursuitConfig(
            seed=0,
            target_policy=args.target_policy,
            target_speed=args.target_speed,
            communication_radius=args.communication_radius,
        )
    )
    _, share_obs, graph_obs = env0.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env0.obs_dim,
        node_feat_dim=graph_obs["node_feat"].shape[-1],
        edge_feat_dim=graph_obs["edge_feat"].shape[-1],
        share_obs_dim=env0.share_obs_dim,
        action_dim=env0.action_dim,
        num_agents=env0.num_agents,
        hidden_dim=128,
        role_dim=8,
        intent_dim=8,
    )
    agent.load_state_dict(torch.load(args.model, map_location="cpu", weights_only=True), strict=False)
    agent.eval()

    counts = np.zeros((NUM_INTENTS, NUM_INTENTS), dtype=np.int64)
    with torch.no_grad():
        for ep in range(args.episodes):
            env = UAVPursuitEnv(
                UAVPursuitConfig(
                    seed=20_000 + ep,
                    target_policy=args.target_policy,
                    target_speed=args.target_speed,
                    communication_radius=args.communication_radius,
                )
            )
            obs, share_obs, graph_obs = env.reset()
            while True:
                graph_batch = stack_graphs([graph_obs])
                actions, _, _, _, _, intent_logits = agent.get_action_and_value(
                    torch.as_tensor(obs[None, ...], dtype=torch.float32),
                    torch.as_tensor(graph_batch["node_feat"], dtype=torch.float32),
                    torch.as_tensor(graph_batch["edge_feat"], dtype=torch.float32),
                    torch.as_tensor(graph_batch["role"], dtype=torch.long),
                    torch.as_tensor(graph_batch["adj"], dtype=torch.float32),
                    torch.as_tensor(share_obs[None, ...], dtype=torch.float32),
                    deterministic=True,
                    intent_label=torch.as_tensor(graph_batch["intent_label"], dtype=torch.long),
                    detach_intent=True,
                    oracle_intent=False,
                )
                labels = np.asarray(graph_batch["intent_label"]).reshape(-1)
                preds = intent_logits.argmax(dim=-1).numpy().reshape(-1)
                for label, pred in zip(labels, preds):
                    counts[int(label), int(pred)] += 1

                obs, share_obs, graph_obs, _, dones, _ = env.step(actions.squeeze(0).numpy())
                if np.all(dones):
                    break

    row_sums = counts.sum(axis=1, keepdims=True)
    norm = np.divide(counts, np.maximum(row_sums, 1), where=row_sums >= 0)
    accuracy = np.trace(counts) / max(1, counts.sum())
    per_class_recall = np.diag(counts) / np.maximum(row_sums.reshape(-1), 1)
    balanced_accuracy = float(per_class_recall.mean())

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["true_intent", "pred_intent", "count"])
        for i, true_name in enumerate(INTENT_NAMES):
            for j, pred_name in enumerate(INTENT_NAMES):
                writer.writerow([true_name, pred_name, int(counts[i, j])])

    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    im = ax.imshow(norm, cmap="Blues", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(NUM_INTENTS), INTENT_NAMES, rotation=30, ha="right")
    ax.set_yticks(range(NUM_INTENTS), INTENT_NAMES)
    ax.set_xlabel("Predicted intent")
    ax.set_ylabel("True intent")
    ax.set_title(f"RI intent confusion, acc={accuracy:.3f}, bal_acc={balanced_accuracy:.3f}")
    for i in range(NUM_INTENTS):
        for j in range(NUM_INTENTS):
            ax.text(j, i, str(counts[i, j]), ha="center", va="center", color="black", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    args.out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out_png, dpi=180)
    plt.close(fig)

    print(
        {
            "accuracy": float(accuracy),
            "balanced_accuracy": balanced_accuracy,
            "per_class_recall": {
                name: float(per_class_recall[i]) for i, name in enumerate(INTENT_NAMES)
            },
            "total": int(counts.sum()),
            "model": str(args.model),
        }
    )
    print(f"saved: {args.out_png}")
    print(f"saved: {args.out_csv}")


if __name__ == "__main__":
    main()
