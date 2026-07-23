from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, RIGMAPPOConfig, make_env, stack_graphs


CSV_COLUMNS = (
    "method",
    "graph_encoder",
    "graph_relation_ablation",
    "graph_message_ablation",
    "graph_input_ablation",
    "total_params",
    "actor_params",
    "critic_params",
    "trainable_params",
    "actor_forward_ms_batch1",
    "actor_forward_ms_batch32",
    "num_agents",
    "num_nodes",
    "node_feat_dim",
    "edge_feat_dim",
    "hidden_dim",
    "role_dim",
    "intent_dim",
    "union_edges_mean",
    "perception_edges_mean",
    "communication_edges_mean",
    "task_support_edges_mean",
    "comm_scalars_per_step_proxy",
)


METHODS = (
    {
        "method": "No-graph MAPPO",
        "graph_encoder": "no_graph",
        "graph_relation_ablation": "none",
        "graph_message_ablation": "none",
        "graph_input_ablation": "none",
    },
    {
        "method": "Single-graph MAPPO",
        "graph_encoder": "single",
        "graph_relation_ablation": "none",
        "graph_message_ablation": "none",
        "graph_input_ablation": "none",
    },
    {
        "method": "Single-graph MAPPO (param-matched)",
        "graph_encoder": "single",
        "graph_relation_ablation": "none",
        "graph_message_ablation": "none",
        "graph_input_ablation": "none",
        "hidden_dim": 240,
    },
    {
        "method": "EA-RG-MAPPO-S",
        "graph_encoder": "multi_relation",
        "graph_relation_ablation": "none",
        "graph_message_ablation": "none",
        "graph_input_ablation": "none",
    },
    {
        "method": "w/o task-support relation",
        "graph_encoder": "multi_relation",
        "graph_relation_ablation": "no_task_support",
        "graph_message_ablation": "none",
        "graph_input_ablation": "none",
    },
    {
        "method": "w/o role-pair gate",
        "graph_encoder": "multi_relation",
        "graph_relation_ablation": "none",
        "graph_message_ablation": "no_role_pair_gate",
        "graph_input_ablation": "none",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report 3DOF model size, actor latency, and graph communication load.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "gate1_safety_fx60_model_costs")
    parser.add_argument("--episodes", type=int, default=64, help="Number of reset samples used for graph-load estimates.")
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--timed-iters", type=int, default=100)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--seed", type=int, default=20260719)
    return parser.parse_args()


def count_params(module: torch.nn.Module) -> int:
    return int(sum(p.numel() for p in module.parameters()))


def count_trainable_params(module: torch.nn.Module) -> int:
    return int(sum(p.numel() for p in module.parameters() if p.requires_grad))


def build_agent(
    graph_encoder: str,
    graph_message_ablation: str,
    graph_input_ablation: str,
    cfg: RIGMAPPOConfig,
) -> tuple[RIGMAPPOAgent, dict[str, np.ndarray], np.ndarray, int]:
    env = make_env(cfg, cfg.seed, training=False)
    obs, share_obs, graph = env.reset()
    num_roles = max(4, int(np.max(graph["role"])) + 1)
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=env.share_obs_dim,
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=num_roles,
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
        graph_encoder=graph_encoder,
        graph_message_ablation=graph_message_ablation,
        graph_input_ablation=graph_input_ablation,
        use_intent_context=False,
    )
    agent.eval()
    return agent, graph, share_obs, env.num_agents


def graph_load_stats(cfg: RIGMAPPOConfig, episodes: int) -> dict[str, float]:
    union_edges = []
    perception_edges = []
    communication_edges = []
    task_support_edges = []
    for idx in range(episodes):
        env = make_env(cfg, cfg.seed + idx, training=False)
        _, _, graph = env.reset()
        union_edges.append(float(np.sum(graph["adj"])))
        relation_adj = graph["relation_adj"]
        perception_edges.append(float(np.sum(relation_adj[0])))
        communication_edges.append(float(np.sum(relation_adj[1])))
        task_support_edges.append(float(np.sum(relation_adj[2])))
    return {
        "union_edges_mean": float(np.mean(union_edges)),
        "perception_edges_mean": float(np.mean(perception_edges)),
        "communication_edges_mean": float(np.mean(communication_edges)),
        "task_support_edges_mean": float(np.mean(task_support_edges)),
    }


def actor_latency_ms(
    agent: RIGMAPPOAgent,
    graph: dict[str, np.ndarray],
    num_agents: int,
    cfg: RIGMAPPOConfig,
    batch_size: int,
    warmup: int,
    timed_iters: int,
) -> float:
    device = torch.device(cfg.device)
    agent.to(device)
    env = make_env(cfg, cfg.seed, training=False)
    obs, _, _ = env.reset()
    stacked = stack_graphs([graph] * batch_size)
    obs_t = torch.as_tensor(np.repeat(obs[None, ...], batch_size, axis=0), dtype=torch.float32, device=device)
    node_t = torch.as_tensor(stacked["node_feat"], dtype=torch.float32, device=device)
    edge_t = torch.as_tensor(stacked["edge_feat"], dtype=torch.float32, device=device)
    role_t = torch.as_tensor(stacked["role"], dtype=torch.long, device=device)
    adj_t = torch.as_tensor(stacked["adj"], dtype=torch.float32, device=device)
    relation_t = torch.as_tensor(stacked["relation_adj"], dtype=torch.float32, device=device)
    intent_t = torch.as_tensor(stacked["intent_label"], dtype=torch.long, device=device)

    with torch.no_grad():
        for _ in range(warmup):
            agent.actor(
                obs_t,
                node_t,
                edge_t,
                role_t,
                adj_t,
                num_agents,
                relation_adj=relation_t,
                intent_label=intent_t,
            )
        start = time.perf_counter()
        for _ in range(timed_iters):
            agent.actor(
                obs_t,
                node_t,
                edge_t,
                role_t,
                adj_t,
                num_agents,
                relation_adj=relation_t,
                intent_label=intent_t,
            )
        elapsed = time.perf_counter() - start
    return float(elapsed * 1000.0 / timed_iters)


def row_for_method(args: argparse.Namespace, method: dict[str, object]) -> dict[str, object]:
    hidden_dim = int(method.get("hidden_dim", args.hidden_dim))
    cfg = RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=args.seed,
        hidden_dim=hidden_dim,
        role_dim=args.role_dim,
        intent_dim=args.intent_dim,
        graph_encoder=str(method["graph_encoder"]),
        graph_relation_ablation=str(method["graph_relation_ablation"]),
        graph_message_ablation=str(method["graph_message_ablation"]),
        graph_input_ablation=str(method["graph_input_ablation"]),
        target_policy="straight",
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        communication_dropout_prob=0.30,
        failed_blue_agent=1,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
        safety_proximity_distance=1000.0,
        safety_proximity_penalty_weight=0.3,
        device=args.device,
    )
    agent, graph, _, num_agents = build_agent(
        str(method["graph_encoder"]),
        str(method["graph_message_ablation"]),
        str(method["graph_input_ablation"]),
        cfg,
    )
    load = graph_load_stats(cfg, args.episodes)
    return {
        **method,
        "total_params": count_params(agent),
        "actor_params": count_params(agent.actor),
        "critic_params": count_params(agent.critic),
        "trainable_params": count_trainable_params(agent),
        "actor_forward_ms_batch1": actor_latency_ms(agent, graph, num_agents, cfg, 1, args.warmup, args.timed_iters),
        "actor_forward_ms_batch32": actor_latency_ms(agent, graph, num_agents, cfg, 32, args.warmup, args.timed_iters),
        "num_agents": num_agents,
        "num_nodes": int(graph["node_feat"].shape[0]),
        "node_feat_dim": int(graph["node_feat"].shape[-1]),
        "edge_feat_dim": int(graph["edge_feat"].shape[-1]),
        "hidden_dim": hidden_dim,
        "role_dim": args.role_dim,
        "intent_dim": args.intent_dim,
        **load,
        "comm_scalars_per_step_proxy": float(load["communication_edges_mean"] * hidden_dim),
    }


def write_markdown(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("# Gate 1 Safety Fixed-Update-60 Model Cost Report\n\n")
        f.write("This report is generated by `scripts/report_3d_model_costs.py`.\n\n")
        f.write("The communication-load value is a proxy: average active directed communication edges multiplied by hidden dimension. The policy uses fixed graph message passing rather than a learned variable-rate communication protocol, so this proxy is intended for fair baseline reporting, not radio-link engineering validation.\n\n")
        f.write("| Method | Actor params | Total params | Batch-1 actor ms | Batch-32 actor ms | Comm edges | Comm scalar proxy |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for row in rows:
            f.write(
                "| {method} | {actor_params} | {total_params} | {actor_forward_ms_batch1:.4f} | "
                "{actor_forward_ms_batch32:.4f} | {communication_edges_mean:.2f} | {comm_scalars_per_step_proxy:.1f} |\n".format(
                    **row
                )
            )
        f.write("\n## Notes\n\n")
        f.write("- `w/o task-support relation` changes the environment relation channel, so its neural parameter count matches the full multi-relation encoder.\n")
        f.write("- `w/o role-pair gate` preserves the same module shape for scale-matched comparison; the role-pair gate is disabled at inference.\n")
        f.write("- `Single-graph MAPPO (param-matched)` increases hidden dimension to 240 so its parameter count is close to the full multi-relation model while preserving the single-graph information structure.\n")
        f.write("- CPU latency should be reported as environment-specific evidence, not as hardware-independent complexity.\n")


def write_latex(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("\\begin{table}[t]\n")
        f.write("\\centering\n")
        f.write("\\caption{Model size, actor inference latency, and communication-load proxy. CPU latency is measured by actor-only forward passes on the current evaluation machine and should be interpreted as implementation-specific evidence.}\n")
        f.write("\\label{tab:gate1-safety-fx60-model-cost}\n")
        f.write("\\small\n")
        f.write("\\resizebox{\\textwidth}{!}{%\n")
        f.write("\\begin{tabular}{lrrrr}\n")
        f.write("\\toprule\n")
        f.write("Method & Actor params & Total params & Batch-1 ms & Comm proxy \\\\\n")
        f.write("\\midrule\n")
        for row in rows:
            f.write(
                "{method} & {actor_params} & {total_params} & {actor_forward_ms_batch1:.3f} & {comm_scalars_per_step_proxy:.1f} \\\\\n".format(
                    **row
                )
            )
        f.write("\\bottomrule\n")
        f.write("\\end{tabular}%\n")
        f.write("}\n")
        f.write("\\end{table}\n")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    rows = [row_for_method(args, method) for method in METHODS]

    csv_path = args.out_dir / "model_costs.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    doc_path = ROOT / "docs" / "gate1_safety_fx60_model_cost_report.md"
    write_markdown(rows, doc_path)
    latex_path = args.out_dir / "model_costs_latex.tex"
    write_latex(rows, latex_path)
    print(f"wrote {csv_path.relative_to(ROOT)}")
    print(f"wrote {doc_path.relative_to(ROOT)}")
    print(f"wrote {latex_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
