"""Read-only S3-D diagnosis of existing graph-encoder checkpoints.

This script never calls backward or an optimizer. It replays the frozen S3 tape
with final checkpoints and records forward-pass branch, adjacency, and
attention diagnostics. It is deliberately separate from training/evaluation
selection executors.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import stack_graphs  # noqa: E402
from scripts.run_phase_s3_development_smoke import agent_for_checkpoint, frozen_env  # noqa: E402


PROTOCOL = "PHASE-S3D-V1"
TAPE_START = 340000
TAPE_EPISODES = 100
SEEDS = (1501, 1502, 1503)
CONDITIONS = ("nominal", "relay_failure")
PROBE_STRIDE = 10
PROBE_BOUNDARY_STEPS = frozenset((43, 44, 45))
RELATION_NAMES = ("perception", "communication", "task_support", "union")
DEVICE_DEFAULT = "cuda" if torch.cuda.is_available() else "cpu"

CHECKPOINTS = {
    "full": {
        "label": "Multi-Relation Full (Role-Gate)",
        "spec": {"encoder": "multi_relation", "hidden": 64, "gate": "relation_conditioned"},
        "root": ROOT / "archival/provenance/phase_s3_cloud_a4f2076/results/development/phase_s3_three_method_smoke/runs/full",
    },
    "simple_full_no_role_gate": {
        "label": "Multi-Relation Full without Role-Gate",
        "spec": {"encoder": "multi_relation", "hidden": 64, "gate": "none"},
        "root": ROOT / "results/development/phase_s3r2_simple_full/runs/simple_full_no_role_gate",
    },
    "matched_single_graph": {
        "label": "Parameter-Matched Single-Graph",
        "spec": {"encoder": "single", "hidden": 115, "gate": "none"},
        "root": ROOT / "archival/provenance/phase_s3_cloud_a4f2076/results/development/phase_s3_three_method_smoke/runs/matched_single_graph",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finite(x: torch.Tensor) -> bool:
    return bool(torch.isfinite(x).all().item())


def entropy_and_max(attention: torch.Tensor, support: torch.Tensor) -> tuple[float, float, float]:
    """Return mean normalized entropy, max weight, and support size.

    ``support`` includes the mandatory self-loop, matching the encoder mask.
    """
    weights = attention.masked_fill(~support, 0.0)
    denom = weights.sum(dim=-1).clamp_min(1e-12)
    weights = weights / denom.unsqueeze(-1)
    logw = torch.where(weights > 0.0, weights.log(), torch.zeros_like(weights))
    ent = -(weights * logw).sum(dim=-1)
    support_n = support.sum(dim=-1).to(dtype=ent.dtype)
    normalized = ent / support_n.clamp_min(2.0).log().clamp_min(1e-12)
    return float(normalized.mean().cpu()), float(weights.max(dim=-1).values.mean().cpu()), float(support_n.mean().cpu())


def encoder_probe(agent, packed: dict[str, np.ndarray], device: torch.device) -> dict:
    actor = agent.actor
    if actor.graph_encoder != "multi_relation":
        return {"graph_encoder": "single", "probe_available": False}

    node_feat = torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device)
    edge_feat = torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device)
    role = torch.as_tensor(packed["role"], dtype=torch.long, device=device)
    relation_adj = torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device)
    union_adj = torch.as_tensor(packed["adj"], dtype=torch.float32, device=device)
    encoder = actor.multi_relation_graph
    with torch.no_grad():
        x = actor.input(torch.cat([node_feat, actor.role_emb(role)], dim=-1))
        x1, attn1 = encoder._apply_layer(x, encoder.layer1, relation_adj, union_adj, edge_feat, role, encoder.fuse1)
        x2, attn2 = encoder._apply_layer(x1, encoder.layer2, relation_adj, union_adj, edge_feat, role, encoder.fuse2)

    rows = []
    for layer_name, layer_x, attention in (("layer1", x1, attn1), ("layer2", x2, attn2)):
        # Recompute branch outputs without changing parameters or state.
        with torch.no_grad():
            branch_outputs = []
            for relation_id, layer in enumerate(encoder.layer1 if layer_name == "layer1" else encoder.layer2):
                branch_outputs.append(layer(x if layer_name == "layer1" else x1, relation_adj[:, relation_id], edge_feat, role)[0])
            global_layer = encoder.global_layer1 if layer_name == "layer1" else encoder.global_layer2
            base_x = x if layer_name == "layer1" else x1
            union_output, _ = global_layer(base_x, union_adj, edge_feat)
            branch_outputs.append(union_output * encoder.global_residual_weight)

        for relation_id, name in enumerate(RELATION_NAMES):
            raw_adj = relation_adj[:, relation_id] if relation_id < 3 else union_adj
            offdiag = raw_adj.clone()
            n = offdiag.shape[-1]
            eye = torch.eye(n, device=device, dtype=torch.bool).unsqueeze(0)
            offdiag = offdiag.masked_fill(eye, 0.0)
            edge_count = offdiag.sum(dim=(-2, -1))
            active_mask = (raw_adj + eye.to(raw_adj.dtype)) > 0.0
            weights = attention[:, relation_id].masked_fill(~active_mask, 0.0)
            weights = weights / weights.sum(dim=-1, keepdim=True).clamp_min(1e-12)
            logw = torch.where(weights > 0.0, weights.log(), torch.zeros_like(weights))
            ent = (-(weights * logw).sum(dim=-1) / active_mask.sum(dim=-1).to(weights.dtype).clamp_min(2.0).log().clamp_min(1e-12)).mean(dim=-1)
            max_attn = weights.max(dim=-1).values.mean(dim=-1)
            support_n = active_mask.sum(dim=-1).to(weights.dtype).mean(dim=-1)
            output = branch_outputs[relation_id]
            node_norm = output.norm(dim=-1).mean(dim=-1)
            for batch_index in range(raw_adj.shape[0]):
                rows.append({
                    "batch_index": batch_index, "layer": layer_name, "relation": name,
                    "active_edge_mean": float(edge_count[batch_index].cpu()),
                    "active_edge_median": float(edge_count[batch_index].cpu()),
                    "empty_graph_ratio": float((edge_count[batch_index] <= 0).cpu()),
                    "branch_norm_mean": float(node_norm[batch_index].cpu()),
                    "branch_norm_median": float(node_norm[batch_index].cpu()),
                    "branch_norm_p95": float(node_norm[batch_index].cpu()),
                    "attention_entropy_normalized": float(ent[batch_index].cpu()),
                    "attention_max_mean": float(max_attn[batch_index].cpu()),
                    "attention_support_mean": float(support_n[batch_index].cpu()),
                    "union_to_relation_norm_ratio": float("nan"),
                    "post_fusion_norm_mean": float("nan"),
                    "finite": finite(output[batch_index:batch_index + 1]) and finite(attention[batch_index:batch_index + 1, relation_id]),
                })

        rel_norm = torch.stack([branch_outputs[i].norm(dim=-1).mean(dim=-1) for i in range(3)], dim=1)
        union_norm = branch_outputs[3].norm(dim=-1).mean(dim=-1)
        ratio = union_norm / rel_norm.mean(dim=1).clamp_min(1e-12)
        post_norm = layer_x.norm(dim=-1).mean(dim=-1)
        union_edges = union_adj.sum(dim=(-2, -1))
        for batch_index in range(x.shape[0]):
            rows.append({
                "batch_index": batch_index, "layer": layer_name, "relation": "union_vs_relation",
                "active_edge_mean": float(union_edges[batch_index].cpu()),
                "active_edge_median": float(union_edges[batch_index].cpu()),
                "empty_graph_ratio": float((union_edges[batch_index] <= 0).cpu()),
                "branch_norm_mean": float(union_norm[batch_index].cpu()),
                "branch_norm_median": float(union_norm[batch_index].cpu()),
                "branch_norm_p95": float(union_norm[batch_index].cpu()),
                "attention_entropy_normalized": float("nan"), "attention_max_mean": float("nan"),
                "attention_support_mean": float("nan"),
                "union_to_relation_norm_ratio": float(ratio[batch_index].cpu()),
                "post_fusion_norm_mean": float(post_norm[batch_index].cpu()),
                "finite": finite(layer_x[batch_index:batch_index + 1]),
            })
    return {"graph_encoder": "multi_relation", "probe_available": True, "rows": rows}


def run(args: argparse.Namespace) -> dict:
    out = args.output
    raw_rows: list[dict] = []
    checkpoint_inventory = []
    telemetry_inventory = []
    for method, meta in CHECKPOINTS.items():
        for seed in SEEDS:
            checkpoint = meta["root"] / f"seed{seed}" / "actor_critic_latest.pt"
            if not checkpoint.exists():
                raise FileNotFoundError(checkpoint)
            checkpoint_inventory.append({"method": method, "seed": seed, "path": str(checkpoint), "sha256": sha256(checkpoint)})
            train_log = checkpoint.parent / "train_log.csv"
            if train_log.exists():
                telemetry_inventory.append({"method": method, "seed": seed, "path": str(train_log), "sha256": sha256(train_log), "separate_actor_critic_gradients": False})

            spec = meta["spec"]
            agent = agent_for_checkpoint(spec, checkpoint, seed)
            device = next(agent.parameters()).device
            for condition in CONDITIONS:
                failure = condition == "relay_failure"
                batch_size = 20
                for batch_start in range(0, TAPE_EPISODES, batch_size):
                    episode_ids = [TAPE_START + i for i in range(batch_start, min(TAPE_EPISODES, batch_start + batch_size))]
                    envs = [frozen_env(eid, failure) for eid in episode_ids]
                    states = [env.reset() for env in envs]
                    active = [True] * len(envs)
                    timestep = 0
                    while any(active):
                        indices = [i for i, flag in enumerate(active) if flag]
                        packed = stack_graphs([states[i][2] for i in indices])
                        probe = encoder_probe(agent, packed, device) if (timestep % PROBE_STRIDE == 0 or timestep in PROBE_BOUNDARY_STEPS) else {"probe_available": False}
                        if probe.get("probe_available"):
                            for row in probe["rows"]:
                                raw_rows.append({
                                    "method": method, "seed": seed, "condition": condition,
                                    "development_episode_id": episode_ids[indices[row["batch_index"]]], "timestep": timestep,
                                    **{k: v for k, v in row.items() if k != "batch_index"},
                                })
                        if args.reset_only:
                            for env_index in indices:
                                active[env_index] = False
                            continue
                        with torch.no_grad():
                            action, *_ = agent.get_action_and_value(
                                torch.as_tensor(np.stack([states[i][0] for i in indices]), dtype=torch.float32, device=device),
                                torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device),
                                torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device),
                                torch.as_tensor(packed["role"], dtype=torch.long, device=device),
                                torch.as_tensor(packed["adj"], dtype=torch.float32, device=device),
                                torch.as_tensor(np.stack([states[i][1] for i in indices]), dtype=torch.float32, device=device),
                                relation_adj=torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device),
                                deterministic=True,
                                intent_label=torch.as_tensor(packed["intent_label"], dtype=torch.long, device=device),
                            )
                        action_batch = action.cpu().numpy()
                        for action_index, env_index in enumerate(indices):
                            obs, share, graph, _, dones, _ = envs[env_index].step(action_batch[action_index])
                            states[env_index] = (obs, share, graph)
                            if np.all(dones):
                                active[env_index] = False
                        timestep += 1
            del agent
            if device.type == "cuda":
                torch.cuda.empty_cache()

    write_csv(out / "raw_forward_probe.csv", raw_rows)
    summary = []
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in raw_rows:
        grouped[(row["method"], row["seed"], row["condition"], row["layer"], row["relation"])].append(row)
    for key, rows in sorted(grouped.items()):
        method, seed, condition, layer, relation = key
        numeric = {k: [float(r.get(k, float("nan"))) for r in rows if r.get(k) not in (None, "") and math.isfinite(float(r.get(k, float("nan"))))] for k in ("active_edge_mean", "empty_graph_ratio", "branch_norm_mean", "branch_norm_median", "attention_entropy_normalized", "attention_max_mean", "attention_support_mean", "union_to_relation_norm_ratio", "post_fusion_norm_mean")}
        summary.append({"method": method, "seed": seed, "condition": condition, "layer": layer, "relation": relation, "rows": len(rows), **{f"{k}_mean": float(np.mean(v)) if v else float("nan") for k, v in numeric.items()}})
    write_csv(out / "summary_by_seed_condition.csv", summary)
    (out / "checkpoint_inventory.json").write_text(json.dumps(checkpoint_inventory, indent=2) + "\n", encoding="utf-8")
    (out / "telemetry_inventory.json").write_text(json.dumps(telemetry_inventory, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "protocol": PROTOCOL, "training_started": False, "backward_called": False, "optimizer_step_called": False,
        "tape_start": TAPE_START, "episodes_per_condition": TAPE_EPISODES, "seeds": list(SEEDS),
        "probe_stride": PROBE_STRIDE, "probe_boundary_steps": sorted(PROBE_BOUNDARY_STEPS),
        "methods": list(CHECKPOINTS), "raw_rows": len(raw_rows), "summary_rows": len(summary),
        "reset_only": bool(args.reset_only),
        "separate_actor_critic_gradient_history_available": False,
        "checkpoint_inventory": checkpoint_inventory, "telemetry_inventory": telemetry_inventory,
        "status": "completed",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results/development/phase_s3d_encoder_diagnosis")
    parser.add_argument("--device", default=DEVICE_DEFAULT, choices=("cpu", "cuda"))
    parser.add_argument("--episodes", type=int, default=TAPE_EPISODES)
    parser.add_argument("--reset-only", action="store_true")
    args = parser.parse_args()
    if args.episodes != TAPE_EPISODES:
        raise SystemExit("S3-D requires the frozen 100-episode tape; no tape resizing is permitted")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    run(args)


if __name__ == "__main__":
    main()
