from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.gat_mappo.simple_gat_mappo import GATMAPPOAgent, stack_graphs as stack_gat_graphs
from algorithms.mappo.simple_mappo import MAPPOAgent
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs as stack_ri_graphs
from envs import UAVPursuitConfig, UAVPursuitEnv
from scripts.evaluate_final_comm_300 import FINAL_RUNS


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def std(values: list[float]) -> float:
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def make_env(
    seed: int,
    target_policy: str,
    target_speed: float,
    radius: float,
    dropout_prob: float,
) -> UAVPursuitEnv:
    return UAVPursuitEnv(
        UAVPursuitConfig(
            seed=seed,
            target_policy=target_policy,
            target_speed=target_speed,
            communication_radius=radius,
            communication_dropout_prob=dropout_prob,
        )
    )


def evaluate_mappo(
    model_path: Path,
    episodes: int,
    target_policy: str,
    target_speed: float,
    radius: float,
    dropout_prob: float,
) -> dict:
    env0 = make_env(0, target_policy, target_speed, radius, dropout_prob)
    agent = MAPPOAgent(env0.obs_dim, env0.share_obs_dim, env0.action_dim, 128)
    agent.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    agent.eval()
    records = []
    with torch.no_grad():
        for ep in range(episodes):
            env = make_env(40_000 + ep, target_policy, target_speed, radius, dropout_prob)
            obs, share_obs, _ = env.reset()
            while True:
                actions, _, _, _ = agent.get_action_and_value(
                    torch.as_tensor(obs, dtype=torch.float32),
                    torch.as_tensor(share_obs, dtype=torch.float32),
                    deterministic=True,
                )
                obs, share_obs, _, _, dones, info = env.step(actions.numpy())
                if np.all(dones):
                    records.append(info)
                    break
    return summarize_records(records)


def evaluate_gat(
    model_path: Path,
    episodes: int,
    target_policy: str,
    target_speed: float,
    radius: float,
    dropout_prob: float,
) -> dict:
    env0 = make_env(0, target_policy, target_speed, radius, dropout_prob)
    _, share_obs, graph_obs = env0.reset()
    agent = GATMAPPOAgent(
        obs_dim=env0.obs_dim,
        node_feat_dim=graph_obs["node_feat"].shape[-1],
        share_obs_dim=env0.share_obs_dim,
        action_dim=env0.action_dim,
        num_agents=env0.num_agents,
        hidden_dim=128,
        role_dim=8,
    )
    agent.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    agent.eval()
    records = []
    with torch.no_grad():
        for ep in range(episodes):
            env = make_env(40_000 + ep, target_policy, target_speed, radius, dropout_prob)
            obs, share_obs, graph_obs = env.reset()
            while True:
                graph_batch = stack_gat_graphs([graph_obs])
                actions, _, _, _, _ = agent.get_action_and_value(
                    torch.as_tensor(obs[None, ...], dtype=torch.float32),
                    torch.as_tensor(graph_batch["node_feat"], dtype=torch.float32),
                    torch.as_tensor(graph_batch["role"], dtype=torch.long),
                    torch.as_tensor(graph_batch["adj"], dtype=torch.float32),
                    torch.as_tensor(share_obs[None, ...], dtype=torch.float32),
                    deterministic=True,
                )
                obs, share_obs, graph_obs, _, dones, info = env.step(actions.squeeze(0).numpy())
                if np.all(dones):
                    records.append(info)
                    break
    return summarize_records(records)


def evaluate_ri(
    model_path: Path,
    episodes: int,
    target_policy: str,
    target_speed: float,
    radius: float,
    dropout_prob: float,
) -> dict:
    env0 = make_env(0, target_policy, target_speed, radius, dropout_prob)
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
    state = torch.load(model_path, map_location="cpu", weights_only=True)
    agent.load_state_dict(state, strict=False)
    agent.eval()
    records = []
    intent_correct, intent_total = 0, 0
    with torch.no_grad():
        for ep in range(episodes):
            env = make_env(40_000 + ep, target_policy, target_speed, radius, dropout_prob)
            obs, share_obs, graph_obs = env.reset()
            while True:
                graph_batch = stack_ri_graphs([graph_obs])
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
                pred = intent_logits.argmax(dim=-1).numpy()
                intent_correct += int((pred == graph_batch["intent_label"]).sum())
                intent_total += int(np.prod(graph_batch["intent_label"].shape))
                obs, share_obs, graph_obs, _, dones, info = env.step(actions.squeeze(0).numpy())
                if np.all(dones):
                    records.append(info)
                    break
    result = summarize_records(records)
    result["intent_accuracy"] = float(intent_correct / max(1, intent_total))
    return result


def summarize_records(records: list[dict]) -> dict:
    return {
        "success_rate": float(np.mean([r["success"] for r in records])),
        "collision_rate": float(np.mean([r["collision"] for r in records])),
        "timeout_rate": float(np.mean([r["timeout"] for r in records])),
        "avg_steps": float(np.mean([r["step"] for r in records])),
        "avg_mean_distance": float(np.mean([r["mean_distance"] for r in records])),
    }


def evaluate_run(
    run: dict,
    episodes: int,
    target_policy: str,
    target_speed: float,
    radius: float,
    dropout_prob: float,
) -> dict:
    model = ROOT / run["model"]
    if run["kind"] == "mappo":
        result = evaluate_mappo(model, episodes, target_policy, target_speed, radius, dropout_prob)
    elif run["kind"] == "gat":
        result = evaluate_gat(model, episodes, target_policy, target_speed, radius, dropout_prob)
    elif run["kind"] == "ri":
        result = evaluate_ri(model, episodes, target_policy, target_speed, radius, dropout_prob)
    else:
        raise ValueError(f"unknown run kind: {run['kind']}")
    return {
        "method": run["method"],
        "seed": run["seed"],
        "kind": run["kind"],
        "model": str(run["model"]),
        "episodes": episodes,
        "target_policy": target_policy,
        "target_speed": target_speed,
        "radius": radius,
        "comm_dropout_prob": dropout_prob,
        "success_rate": result["success_rate"],
        "collision_rate": result["collision_rate"],
        "timeout_rate": result["timeout_rate"],
        "avg_steps": result["avg_steps"],
        "avg_mean_distance": result["avg_mean_distance"],
        "intent_accuracy": result.get("intent_accuracy", ""),
    }


def write_rows(rows: list[dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict]) -> list[dict]:
    summary = []
    methods = list(dict.fromkeys(row["method"] for row in rows))
    radii = sorted({float(row["radius"]) for row in rows})
    dropouts = sorted({float(row["comm_dropout_prob"]) for row in rows})
    for method in methods:
        for radius in radii:
            for dropout in dropouts:
                group = [
                    row
                    for row in rows
                    if row["method"] == method
                    and abs(float(row["radius"]) - radius) < 1e-9
                    and abs(float(row["comm_dropout_prob"]) - dropout) < 1e-9
                ]
                summary.append(
                    {
                        "method": method,
                        "episodes": group[0]["episodes"],
                        "radius": radius,
                        "comm_dropout_prob": dropout,
                        "success_mean": mean([float(row["success_rate"]) for row in group]),
                        "success_std": std([float(row["success_rate"]) for row in group]),
                        "collision_mean": mean([float(row["collision_rate"]) for row in group]),
                        "collision_std": std([float(row["collision_rate"]) for row in group]),
                        "timeout_mean": mean([float(row["timeout_rate"]) for row in group]),
                        "timeout_std": std([float(row["timeout_rate"]) for row in group]),
                        "avg_steps_mean": mean([float(row["avg_steps"]) for row in group]),
                        "avg_steps_std": std([float(row["avg_steps"]) for row in group]),
                        "n": len(group),
                    }
                )
    return summary


def fmt(mean_value: float, std_value: float) -> str:
    return f"{mean_value:.3f}$\\pm${std_value:.3f}"


def write_latex(summary: list[dict], out_tex: Path) -> None:
    episodes = int(summary[0]["episodes"]) if summary else 0
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        f"\\caption{{Evaluation-time communication-dropout robustness diagnostic. Results are reported as mean$\\pm$std over three seeds with {episodes} episodes per seed.}}",
        "\\label{tab:comm_dropout_robustness}",
        "\\begin{tabular}{lcccc}",
        "\\toprule",
        "Method & Radius & Dropout prob. & Success $\\uparrow$ & Collision $\\downarrow$ \\\\",
        "\\midrule",
    ]
    current = None
    for row in summary:
        if current is not None and row["method"] != current:
            lines.append("\\midrule")
        current = row["method"]
        lines.append(
            f"{row['method']} & {float(row['radius']):.0f} & {float(row['comm_dropout_prob']):.2f} & "
            f"{fmt(float(row['success_mean']), float(row['success_std']))} & "
            f"{fmt(float(row['collision_mean']), float(row['collision_std']))} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""])
    out_tex.write_text("\n".join(lines), encoding="utf-8")


def write_notes(summary: list[dict], out_md: Path) -> None:
    by_key = {
        (row["method"], float(row["radius"]), float(row["comm_dropout_prob"])): row
        for row in summary
    }
    lines = [
        "# Communication-Dropout Robustness Diagnostic",
        "",
        "Purpose:",
        "",
        "```text",
        "Evaluate trained policies under stochastic pursuer-pursuer communication-link dropout without retraining.",
        "The diagnostic masks both teammate local-observation slots and graph adjacency/edge reachability.",
        "The target observation node is retained; this experiment only degrades pursuer-pursuer communication links.",
        "```",
        "",
        "## Summary",
        "",
        "| Method | Radius | Dropout | Success mean | Collision mean |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['method']} | {float(row['radius']):.0f} | {float(row['comm_dropout_prob']):.2f} | "
            f"{float(row['success_mean']):.3f} | {float(row['collision_mean']):.3f} |"
        )

    lines.extend(["", "## Delta from No-Dropout Diagnostic Baseline", ""])
    lines.append("| Method | Radius | Dropout | Delta success | Delta collision |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in summary:
        dropout = float(row["comm_dropout_prob"])
        if dropout == 0.0:
            continue
        base = by_key[(row["method"], float(row["radius"]), 0.0)]
        lines.append(
            f"| {row['method']} | {float(row['radius']):.0f} | {dropout:.2f} | "
            f"{float(row['success_mean']) - float(base['success_mean']):+.3f} | "
            f"{float(row['collision_mean']) - float(base['collision_mean']):+.3f} |"
        )

    lines.extend(
        [
            "",
            "## Use in Paper",
            "",
            "```text",
            "Use this as an appendix-level robustness diagnostic only.",
            "Do not merge it with the final 300-episode main table, because it uses a smaller evaluation budget and an additional communication-dropout perturbation.",
            "```",
            "",
        ]
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--radii", type=float, nargs="+", default=[4.0, 8.0])
    parser.add_argument("--dropout-probs", type=float, nargs="+", default=[0.0, 0.25, 0.50])
    parser.add_argument("--out-csv", type=Path, default=Path("results/comm_dropout_robustness_eval.csv"))
    parser.add_argument("--summary-csv", type=Path, default=Path("results/comm_dropout_robustness_summary.csv"))
    parser.add_argument("--notes-md", type=Path, default=Path("results/comm_dropout_robustness_notes.md"))
    parser.add_argument("--latex-table", type=Path, default=Path("results/latex_comm_dropout_robustness_table.tex"))
    args = parser.parse_args()

    rows = []
    for run in FINAL_RUNS:
        for radius in args.radii:
            for dropout in args.dropout_probs:
                row = evaluate_run(
                    run,
                    args.episodes,
                    args.target_policy,
                    args.target_speed,
                    radius,
                    dropout,
                )
                rows.append(row)
                print(row, flush=True)
                write_rows(rows, args.out_csv)

    summary = summarize(rows)
    write_rows(summary, args.summary_csv)
    write_latex(summary, args.latex_table)
    write_notes(summary, args.notes_md)
    print(f"saved: {args.out_csv}")
    print(f"saved: {args.summary_csv}")
    print(f"saved: {args.latex_table}")
    print(f"saved: {args.notes_md}")


if __name__ == "__main__":
    main()
