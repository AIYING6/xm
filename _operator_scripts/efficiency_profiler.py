# efficiency_profiler.py
# Efficiency profiling core for FORMAL_EFFICIENCY_PROTOCOL_V1_5.
#
# Provides per-method joint-decision timing (3-agent team action), CUDA-synced
# raw latencies, resettable memory stats, and communication counters, with a
# single joint-decision unit across Full / w/o RPG / MAPPO / HAPPO /
# param_matched_single.
#
# Importable library used by:
#   run_efficiency_smoke_v1_5.py   (phase-2 smoke, small budgets)
#   run_efficiency_v1_5.py         (phase-3 formal profiling, frozen budgets)
from __future__ import annotations

import json
import platform
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import torch

# ---------------------------------------------------------------- hardware ----

def hardware_snapshot() -> dict[str, Any]:
    tf32 = torch.backends.cuda.matmul.allow_tf32 if hasattr(torch.backends.cuda, "matmul") else None
    cudnn_tf32 = torch.backends.cudnn.allow_tf32 if hasattr(torch.backends.cudnn, "allow_tf32") else None
    return {
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "cuda_version": torch.version.cuda,
        "pytorch_version": torch.__version__,
        "gpu_driver": None,  # filled by nvidia-smi if available
        "cpu": platform.processor(),
        "ram_gb": None,  # filled by OS query
        "platform": platform.platform(),
        "precision": "FP32",
        "tf32_matmul": tf32,
        "tf32_cudnn": cudnn_tf32,
        "compile": False,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ------------------------------------------------------------- joint timing ----

@dataclass
class LatencyResult:
    batch: int
    method: str
    latencies_ms: list[float] = field(default_factory=list)
    decisions: int = 0

    def summary(self) -> dict[str, float]:
        a = np.array(self.latencies_ms, dtype=float)
        return {
            "mean_ms": float(a.mean()),
            "median_ms": float(np.median(a)),
            "p95_ms": float(np.percentile(a, 95)),
            "p99_ms": float(np.percentile(a, 99)),
            "sd_ms": float(a.std(ddof=1)) if a.size > 1 else 0.0,
            "decisions_per_s": 1000.0 / float(a.mean()) if a.size else 0.0,
            "n": int(a.size),
        }


def time_joint_forward(fn, reps: int, device: str = "cuda") -> list[float]:
    """Time fn() as ONE joint team decision with CUDA sync around it.

    fn must produce the full 3-agent joint action. Returns raw per-call ms.
    """
    out = []
    for _ in range(reps):
        if device == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        fn()
        if device == "cuda":
            torch.cuda.synchronize()
        t1 = time.perf_counter()
        out.append((t1 - t0) * 1000.0)
    return out


# --------------------------------------------------------------- memory -------

@dataclass
class MemoryResult:
    peak_allocated_mb: float
    peak_reserved_mb: float


def reset_memory(device: str = "cuda") -> None:
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()


def snapshot_memory(device: str = "cuda") -> MemoryResult:
    if device != "cuda":
        return MemoryResult(0.0, 0.0)
    return MemoryResult(
        peak_allocated_mb=torch.cuda.max_memory_allocated() / 1e6,
        peak_reserved_mb=torch.cuda.max_memory_reserved() / 1e6,
    )


# ------------------------------------------------------------- communication ---

@dataclass
class CommStats:
    graph_candidate_edges: int = 0      # model attention edges (may include self-loop)
    physical_comm_edges: int = 0        # i != j and comm_adj>0
    available_physical_edges: int = 0   # same as physical for a fixed adj (kept for clarity)
    actual_target_messages: int = 0     # agent-to-agent target messages sent
    edge_feature_dim: int = 0
    continuous_payload_dim: int = 0     # 7 (pos3 + vel3 + confidence)
    metadata_fields: int = 0            # 4 (source, generation_step, delivery_step, hop_count)
    variable_path: bool = True


def collect_comm_stats(env, adj: torch.Tensor | None = None,
                       relation_adj: torch.Tensor | None = None) -> CommStats:
    """Collect communication counters from the GRAPH adj (not env.comm_adj,
    which is identity-only right after reset).

    The env graph is 4-node (3 blue + 1 red); only the blue 3x3 block counts
    for agent-to-agent communication (red is the target, not a UAV).

    adj: stacked graph "adj" (batch, n, n) or (n, n); includes self-loop.
    relation_adj: multi_relation adjacency (3, n, n) - candidate edge mask.
    """
    s = CommStats()
    n_blue = env.num_agents  # 3 blue UAVs
    if adj is not None:
        adj_np = np.asarray(adj.cpu().numpy() if torch.is_tensor(adj) else adj)
        if adj_np.ndim == 3:
            adj_np = adj_np[0]
        adj_blue = adj_np[:n_blue, :n_blue]
    elif hasattr(env, "comm_adj"):
        adj_blue = np.asarray(env.comm_adj)[:n_blue, :n_blue]
    else:
        adj_blue = np.ones((n_blue, n_blue))
    if relation_adj is not None:
        rel = np.asarray(relation_adj.cpu().numpy() if torch.is_tensor(relation_adj) else relation_adj)
        if rel.ndim == 4:  # (batch, n_rel, n, n)
            rel = rel[0]
        # candidate edges: any relation active over the blue block (3 x 3 x n_rel)
        cand = (np.abs(rel[:, :n_blue, :n_blue]).sum(axis=0) != 0)
    else:
        cand = (adj_blue != 0)
    s.graph_candidate_edges = int(cand.sum())
    # physical comm edges: i != j and adj>0 (no self-loop) over blue block
    mask = np.ones((n_blue, n_blue), dtype=bool)
    np.fill_diagonal(mask, False)
    s.physical_comm_edges = int((mask & (adj_blue != 0)).sum())
    s.available_physical_edges = s.physical_comm_edges
    # actual messages: pending target messages queue length
    msgs = 0
    for attr in ("pending_target_messages", "target_msg_queue", "message_queue"):
        if hasattr(env, attr):
            q = getattr(env, attr)
            msgs = len(q) if isinstance(q, (list, dict)) else int(q)
            break
    s.actual_target_messages = msgs
    s.edge_feature_dim = 17  # frozen (GAT edge feature dim)
    s.continuous_payload_dim = 7  # pos3+vel3+confidence
    s.metadata_fields = 4
    s.variable_path = True
    return s


def comm_stats_to_dict(s: CommStats) -> dict[str, Any]:
    return {
        "graph_candidate_edges": s.graph_candidate_edges,
        "physical_comm_edges": s.physical_comm_edges,
        "available_physical_edges": s.available_physical_edges,
        "actual_target_messages": s.actual_target_messages,
        "edge_feature_dim": s.edge_feature_dim,
        "continuous_payload_dim": s.continuous_payload_dim,
        "metadata_fields": s.metadata_fields,
        "variable_path": s.variable_path,
    }
