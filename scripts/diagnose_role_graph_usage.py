from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_ri_gmappo_3d import build_agent, build_config  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import make_env, stack_graphs  # noqa: E402


RELATION_NAMES = ("perception", "communication", "task_support", "global")
ROLE_NAMES = {
    0: "scout",
    1: "relay",
    2: "attacker",
    3: "interceptor",
    4: "target",
}


def mean(values: Iterable[float], empty: float = 0.0) -> float:
    values = list(values)
    return float(np.mean(values)) if values else empty


def attention_mass(attn: np.ndarray, mask: np.ndarray) -> float:
    if attn.size == 0:
        return 0.0
    denom = float(np.sum(attn))
    if denom <= 1e-12:
        return 0.0
    return float(np.sum(attn * mask) / denom)


def relation_step_metrics(attn: np.ndarray, relation_adj: np.ndarray, node_failure_active: float) -> dict[str, float]:
    metrics: dict[str, float] = {"node_failure_active": float(node_failure_active)}
    union = np.clip(np.max(relation_adj, axis=0), 0.0, 1.0)
    for relation_id, name in enumerate(RELATION_NAMES):
        relation_attn = attn[relation_id]
        mask = union if name == "global" else relation_adj[relation_id]
        metrics[f"{name}_attention_mass"] = attention_mass(relation_attn, mask)
        metrics[f"{name}_edge_density"] = float(np.mean(mask > 0.5))
    metrics["task_support_active"] = float(np.max(relation_adj[2]) > 0.5)
    metrics["communication_active"] = float(np.max(relation_adj[1]) > 0.5)
    metrics["perception_active"] = float(np.max(relation_adj[0]) > 0.5)
    return metrics


def summarize_episode(step_metrics: list[dict[str, float]], final_info: dict[str, float], episode: int, seed: int) -> dict[str, float | int]:
    row: dict[str, float | int] = {
        "episode": episode,
        "seed": seed,
        "success": float(final_info.get("success", 0.0)),
        "chain_closed": float(final_info.get("chain_closed", 0.0)),
        "collision": float(final_info.get("collision", 0.0)),
        "timeout": float(final_info.get("timeout", 0.0)),
        "steps": float(final_info.get("step", 0.0)),
    }
    for relation in RELATION_NAMES:
        key = f"{relation}_attention_mass"
        row[f"{relation}_attention_mass_mean"] = mean(float(m[key]) for m in step_metrics)
        row[f"{relation}_attention_mass_during_failure"] = mean(
            float(m[key]) for m in step_metrics if float(m["node_failure_active"]) > 0.5
        )
        row[f"{relation}_edge_density_mean"] = mean(float(m[f"{relation}_edge_density"]) for m in step_metrics)
    for key in ("task_support_active", "communication_active", "perception_active"):
        row[f"{key}_rate"] = mean(float(m[key]) for m in step_metrics)
    return row


def gate_rows(agent) -> list[dict[str, float | int | str]]:
    actor = agent.actor
    if getattr(actor, "graph_encoder", "") != "multi_relation":
        return []
    graph = actor.multi_relation_graph
    rows: list[dict[str, float | int | str]] = []
    for layer_name in ("layer1", "layer2"):
        layers = getattr(graph, layer_name)
        for relation_id, layer in enumerate(layers):
            weight = torch.sigmoid(layer.role_pair_gate.weight.detach().cpu()).numpy()
            num_roles = int(layer.num_roles)
            for receiver_role in range(num_roles):
                for sender_role in range(num_roles):
                    pair_index = receiver_role * num_roles + sender_role
                    values = weight[pair_index]
                    rows.append(
                        {
                            "layer": layer_name,
                            "relation": RELATION_NAMES[relation_id],
                            "receiver_role": receiver_role,
                            "receiver_role_name": ROLE_NAMES.get(receiver_role, str(receiver_role)),
                            "sender_role": sender_role,
                            "sender_role_name": ROLE_NAMES.get(sender_role, str(sender_role)),
                            "gate_mean": float(np.mean(values)),
                            "gate_std": float(np.std(values)),
                            "gate_min": float(np.min(values)),
                            "gate_max": float(np.max(values)),
                            "gate_abs_delta_from_0_5": float(abs(np.mean(values) - 0.5)),
                        }
                    )
    return rows


def run_diagnostics(args: argparse.Namespace) -> tuple[list[dict[str, float | int]], list[dict[str, float | int | str]]]:
    cfg = build_config(args)
    agent, _ = build_agent(args, cfg)
    device = torch.device(args.device)
    episode_rows: list[dict[str, float | int]] = []
    if args.graph_encoder != "multi_relation":
        raise ValueError("role-graph usage diagnostics require --graph-encoder multi_relation")

    with torch.no_grad():
        for episode in range(args.episodes):
            seed = args.base_seed + episode
            env = make_env(cfg, seed, training=False)
            obs, share_obs, graph = env.reset()
            step_metrics: list[dict[str, float]] = []
            while True:
                g = stack_graphs([graph])
                actions, _, _, _, attn, _, _ = agent.get_action_and_value(
                    torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                    torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(g["role"], dtype=torch.long, device=device),
                    torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                    torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                    relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device),
                    deterministic=not args.stochastic,
                    intent_label=torch.as_tensor(g["intent_label"], dtype=torch.long, device=device),
                    detach_intent=False,
                    oracle_intent=False,
                )
                obs, share_obs, graph, _, dones, info = env.step(actions.squeeze(0).cpu().numpy())
                step_metrics.append(
                    relation_step_metrics(
                        attn.squeeze(0).detach().cpu().numpy(),
                        g["relation_adj"][0],
                        float(info.get("node_failure_active", 0.0)),
                    )
                )
                if np.all(dones):
                    episode_rows.append(summarize_episode(step_metrics, info, episode, seed))
                    break
    return episode_rows, gate_rows(agent)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, episode_rows: list[dict], gate_rows_: list[dict], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_success: dict[str, list[dict]] = defaultdict(list)
    for row in episode_rows:
        by_success["success" if float(row["success"]) > 0.5 else "failure"].append(row)

    lines = [
        "# Role-Graph Usage Diagnostics",
        "",
        f"- checkpoint: `{args.checkpoint}`",
        f"- episodes: `{args.episodes}`",
        f"- target policy: `{args.target_policy}`",
        f"- dropout: `{args.communication_dropout_prob}`",
        f"- delay: `{args.message_delay_steps}`",
        f"- failed blue agent: `{args.failed_blue_agent}`",
        f"- multi-relation global residual weight: `{args.multi_relation_global_residual_weight}`",
        "",
        "## Episode Means",
        "",
        "| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group, rows in (("all", episode_rows), ("success", by_success["success"]), ("failure", by_success["failure"])):
        lines.append(
            "| "
            + " | ".join(
                [
                    group,
                    str(len(rows)),
                    f"{mean(float(r['success']) for r in rows):.4f}",
                    f"{mean(float(r['task_support_attention_mass_mean']) for r in rows):.4f}",
                    f"{mean(float(r['communication_attention_mass_mean']) for r in rows):.4f}",
                    f"{mean(float(r['perception_attention_mass_mean']) for r in rows):.4f}",
                    f"{mean(float(r['global_attention_mass_mean']) for r in rows):.4f}",
                ]
            )
            + " |"
        )

    max_gate_delta = max((float(r["gate_abs_delta_from_0_5"]) for r in gate_rows_), default=0.0)
    mean_gate_delta = mean(float(r["gate_abs_delta_from_0_5"]) for r in gate_rows_)
    lines.extend(
        [
            "",
            "## Gate Summary",
            "",
            f"- mean absolute gate deviation from 0.5: `{mean_gate_delta:.6f}`",
            f"- max absolute gate deviation from 0.5: `{max_gate_delta:.6f}`",
            "",
            "Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--base-seed", type=int, default=31_000)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--communication-range-scale", type=float, default=1.0)
    parser.add_argument("--communication-dropout-prob", type=float, default=0.30)
    parser.add_argument("--message-delay-steps", type=int, default=2)
    parser.add_argument("--radar-dropout-prob", type=float, default=0.0)
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--target-prior-position", type=float, nargs=3, default=(10_000.0, 0.0, 5_000.0))
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--failed-blue-agent", type=int, default=1)
    parser.add_argument("--node-failure-start-step", type=int, default=40)
    parser.add_argument("--node-failure-duration-steps", type=int, default=80)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--allow-random-policy", action="store_true")
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--graph-encoder", choices=("no_graph", "single", "multi_relation"), default="multi_relation")
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--multi-relation-global-residual-weight", type=float, default=1.0)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "role_graph_diagnostics")
    args = parser.parse_args()

    episode_rows, gate_rows_ = run_diagnostics(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    episode_csv = args.out_dir / "episode_relation_attention.csv"
    gate_csv = args.out_dir / "role_pair_gate.csv"
    summary_md = args.out_dir / "role_graph_diagnostics.md"
    write_csv(episode_csv, episode_rows)
    write_csv(gate_csv, gate_rows_)
    write_summary(summary_md, episode_rows, gate_rows_, args)
    print(episode_csv)
    print(gate_csv)
    print(summary_md)


if __name__ == "__main__":
    main()
