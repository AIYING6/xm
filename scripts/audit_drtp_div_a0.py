"""Offline DRTP-DIV-A0 policy/optimization divergence audit.

This program only reads archived ``train_log.csv`` files and archived runtime
states.  It never constructs an environment, calls ``reset``/``step``, or
writes to an experiment-result directory.  Runtime snapshots are used solely
as recorded actor-legal observation banks for deterministic actor forwards.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

# Archives were produced with NumPy 2, whereas the maintained CAC environment
# may expose the NumPy 1 module spelling during forensic work.  This is a
# read-only unpickling compatibility alias, not a conversion of archival data.
import numpy.core as _np_core
import numpy.core.multiarray as _np_multiarray
import numpy.core.numerictypes as _np_numerictypes

sys.modules.setdefault("numpy._core", _np_core)
sys.modules.setdefault("numpy._core.multiarray", _np_multiarray)
sys.modules.setdefault("numpy._core.numerictypes", _np_numerictypes)

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent  # noqa: E402


WINDOWS = ((0, 977, "0_0.25M"), (977, 1954, "0.25_0.5M"),
           (1954, 3907, "0.5_1M"), (3907, 7813, "1_2M"),
           (7813, 11719, "2_3M"), (11719, 39063, "3_10M"))
METRICS = ("loss", "policy_loss", "value_loss", "entropy", "approx_kl",
           "clip_fraction", "grad_norm", "explained_variance", "train_avg_reward")
SEED_CLASS = {1901: "strong", 1902: "weak", 2001: "strong", 2002: "weak", 2003: "strong"}


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def std(xs: list[float]) -> float:
    if not xs:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def read_train(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = []
        for row in csv.DictReader(handle):
            out = {"update": float(row["update"])}
            for key in METRICS:
                raw = row.get(key, "")
                out[key] = float(raw) if raw not in ("", None) else float("nan")
            rows.append(out)
    return rows


def finite(xs: list[float]) -> list[float]:
    return [x for x in xs if math.isfinite(x)]


def runtime_path(root: Path, source: str, arm: str, seed: int, label: str) -> Path:
    if source == "strict":
        base = root / "results/development/drtp_sg_strict_continuous_10m/runs"
    else:
        base = root / "results/heldout/drtp_sg_heldout_v2/runs"
    return base / arm / f"seed{seed}" / f"actor_critic_runtime_state_milestone_{label}.pt"


def load_runtime(path: Path) -> dict:
    return torch.load(path, map_location="cpu", weights_only=False)


def make_agent(state: dict) -> RIGMAPPOAgent:
    obs = state["obs"]
    graph = state["graph_obs"]
    agent = RIGMAPPOAgent(
        obs_dim=obs.shape[-1], node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=state["share_obs"].shape[-1],
        action_dim=27, num_agents=obs.shape[1], num_roles=5, hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        use_intent_context=True,
    )
    agent.load_state_dict(state["model_state"], strict=True)
    if sum(p.numel() for p in agent.parameters()) != 116728:
        raise RuntimeError("unexpected parameter count in archived runtime state")
    return agent.eval()


def probability(agent: RIGMAPPOAgent, bank: dict) -> np.ndarray:
    graph = bank["graph_obs"]
    with torch.no_grad():
        logits, _attn, _intent = agent.actor(
            torch.as_tensor(bank["obs"], dtype=torch.float32),
            torch.as_tensor(graph["node_feat"], dtype=torch.float32),
            torch.as_tensor(graph["edge_feat"], dtype=torch.float32),
            torch.as_tensor(graph["role"], dtype=torch.long),
            torch.as_tensor(graph["adj"], dtype=torch.float32),
            bank["obs"].shape[1], relation_adj=torch.as_tensor(graph["relation_adj"], dtype=torch.float32),
        )
    return torch.softmax(logits, dim=-1).numpy()


def js_divergence(a: np.ndarray, b: np.ndarray) -> float:
    m = (a + b) / 2.0
    kl_a = np.sum(a * (np.log(np.clip(a, 1e-12, 1)) - np.log(np.clip(m, 1e-12, 1))), axis=-1)
    kl_b = np.sum(b * (np.log(np.clip(b, 1e-12, 1)) - np.log(np.clip(m, 1e-12, 1))), axis=-1)
    return float(np.mean((kl_a + kl_b) / 2.0))


def policy_rows(runtime_root: Path) -> list[dict]:
    # Each paired seed uses the UTR 500k runtime observation as a common,
    # actor-legal, recorded bank.  No environment is recreated.
    sources = {1901: "strict", 1902: "strict", 2001: "heldout", 2002: "heldout", 2003: "heldout"}
    labels = ("500k", "1m", "1500k", "2m", "2500k", "3m", "3500k", "4m", "4500k", "5m",
              "5500k", "6m", "6500k", "7m", "7500k", "8m", "8500k", "9m", "9500k", "10m")
    rows = []
    for seed, source in sources.items():
        bank = load_runtime(runtime_path(runtime_root, source, "utr_sg", seed, "500k"))
        for label in labels:
            utr = load_runtime(runtime_path(runtime_root, source, "utr_sg", seed, label))
            drtp = load_runtime(runtime_path(runtime_root, source, "drtp_sg", seed, label))
            p_u, p_d = probability(make_agent(utr), bank), probability(make_agent(drtp), bank)
            ent_u = -np.sum(p_u * np.log(np.clip(p_u, 1e-12, 1)), axis=-1)
            ent_d = -np.sum(p_d * np.log(np.clip(p_d, 1e-12, 1)), axis=-1)
            step = 500_000 if label == "500k" else int(label[:-1]) * 1_000_000 if label.endswith("m") else int(label[:-1]) * 1_000
            rows.append({
                "source_contract": source, "seed": seed, "seed_class": SEED_CLASS[seed],
                "milestone": label, "environment_steps": step, "bank": "paired_utr_500k_runtime_obs",
                "bank_envs": int(bank["obs"].shape[0]), "bank_agents": int(bank["obs"].shape[1]),
                "mean_total_variation": float(np.mean(0.5 * np.sum(np.abs(p_d - p_u), axis=-1))),
                "mean_js_divergence": js_divergence(p_d, p_u),
                "mean_entropy_utr": float(np.mean(ent_u)), "mean_entropy_drtp": float(np.mean(ent_d)),
                "mean_entropy_delta_drtp_minus_utr": float(np.mean(ent_d - ent_u)),
                "greedy_action_disagreement": float(np.mean(np.argmax(p_d, axis=-1) != np.argmax(p_u, axis=-1))),
                "status": "estimated_from_archived_runtime_states",
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args()
    args.artifact_root.mkdir(parents=True, exist_ok=True)
    opt = []
    sources = {1901: "strict", 1902: "strict", 2001: "heldout", 2002: "heldout", 2003: "heldout"}
    for seed, source in sources.items():
        root = args.logs_root / ("results/development/drtp_sg_strict_continuous_10m/runs" if source == "strict" else "results/heldout/drtp_sg_heldout_v2/runs")
        for arm in ("utr_sg", "drtp_sg"):
            rows = read_train(root / arm / f"seed{seed}" / "train_log.csv")
            for lo, hi, window in WINDOWS:
                selected = [r for r in rows if lo < r["update"] <= hi]
                for metric in METRICS:
                    values = finite([r[metric] for r in selected])
                    opt.append({"source_contract": source, "arm": arm, "seed": seed, "seed_class": SEED_CLASS[seed],
                                "window": window, "first_update_exclusive": lo, "last_update_inclusive": hi,
                                "metric": metric, "n_updates": len(values), "mean": mean(values), "std": std(values),
                                "min": min(values) if values else float("nan"), "max": max(values) if values else float("nan")})
    policy = policy_rows(args.runtime_root)
    coordination = [{"status": "not_estimable", "reason": "archives contain episode-level final metrics but no step-level coordination trajectory telemetry; no new rollout authorized"}]
    events = {"optimization": "no event classification is inferred from descriptive logs alone", "policy": "policy distances are archival runtime-state estimates", "coordination": "not estimable without step-level trajectories"}
    for name, rows in (("optimization_timeline.csv", opt), ("policy_distance_timeline.csv", policy), ("coordination_timeline.csv", coordination)):
        fields = sorted({key for row in rows for key in row})
        with (args.artifact_root / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
    (args.artifact_root / "divergence_events.json").write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
