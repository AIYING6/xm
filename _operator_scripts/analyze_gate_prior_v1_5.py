# analyze_gate_prior_v1_5.py
# Gate Prior mechanism analysis, GATE_PRIOR_MECHANISM_PROTOCOL_V1_5 (frozen, + Addendum A).
# Read-only over locked training assets. Produces docs/gate_prior_v1_5_assets/.
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
OUT = ROOT / "docs" / "gate_prior_v1_5_assets"

FULL_RUN = (ROOT / "results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802/ea_rg_mappo_s_gate_prior").resolve()
WOP_RUN = (AB_ROOT / "results/paper_config_runs/formal_ablation_v1.5_ppo_977_20260804/w_o_gate_prior").resolve()
HELD_OUT_SUM = Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/formal_held_out_v1_5_10800_20260807/held_out_v1.5")

METHODS = {"full": FULL_RUN, "w_o_gate_prior": WOP_RUN}
SEEDS = [0, 1, 2]
EVAL_GRID = [1, 100, 200, 300, 400, 500, 600, 700, 800, 900]
CKPT_NODES = [100, 200, 300, 400, 500, 600, 700, 800, 900, 977]
FINAL_WINDOW = [700, 800, 900]
K_CONSEC = 3
GATE_KEYS = [f"actor.multi_relation_graph.layer{l}.{r}.role_pair_gate.weight"
             for l in (1, 2) for r in (0, 1, 2)]
PRIOR_PAIRS = {  # relation -> set((receiver, sender))
    0: {(0, 4), (1, 4), (2, 4), (3, 4)},
    1: {(0, 1), (1, 0), (1, 2), (1, 3), (2, 1), (3, 1)},
    2: {(2, 0), (3, 0), (0, 1), (2, 1), (3, 1), (1, 2), (1, 3)},
}
PRIOR_LOGIT = 0.4
ZERO_LOGIT = 0.0
NUM_ROLES = 5  # 0..4, Embedding 25 pairs
HID = 64


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))


def load_state(ckpt: Path):
    sd = torch.load(ckpt, map_location="cpu", weights_only=False)
    for cand in ("model_state_dict", "state_dict"):
        if isinstance(sd, dict) and cand in sd:
            return sd[cand]
    return sd


def extract_gates(state) -> np.ndarray:
    """Return (6 channels, 25 pairs, 64) logits."""
    arr = np.stack([state[k].numpy() for k in GATE_KEYS if k in state])
    if arr.shape[0] != 6:
        raise RuntimeError(f"expected 6 gate channels, got {arr.shape[0]}")
    return arr


def initial_gate_vector() -> np.ndarray:
    """Analytic update=0 gate: (6, 25) aggregated (pair-mean over 64 dims constant)."""
    vec = np.full((6, 25), ZERO_LOGIT, dtype=float)
    for rel in (0, 1, 2):
        for (recv, send) in PRIOR_PAIRS.get(rel, set()):
            idx = recv * NUM_ROLES + send
            for layer in (0, 1):
                vec[2 * layer + rel, idx] = PRIOR_LOGIT
    return sigmoid(vec).ravel()


def aggregate_gates(logits: np.ndarray) -> np.ndarray:
    """(6,25,64) logits -> (150,) sigmoid gate values (pair mean over 64 dims)."""
    return sigmoid(logits.mean(axis=2)).ravel()


def load_train_log(path: Path):
    rows = []
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    ev = {}
    for r in rows:
        u = int(r["update"])
        if r.get("eval_success_rate", "").strip() != "":
            ev[u] = float(r["eval_success_rate"])
    return ev


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- Block 1: training stability ----------------
    stab_rows = []          # per method per eval point
    per_method = {}
    for m, base in METHODS.items():
        evals = {s: load_train_log(base / f"ppo_seed{s}_1m" / "train_log.csv") for s in SEEDS}
        for u in EVAL_GRID:
            vals = [evals[s][u] for s in SEEDS if u in evals[s]]
            if len(vals) != 3:
                problems.append(f"{m}: eval point {u} missing seed data ({len(vals)}/3)")
                continue
            a = np.array(vals, dtype=float)
            stab_rows.append({
                "method": m, "update": u, "n": 3,
                "mean": float(a.mean()), "sd": float(a.std(ddof=1)),
                "worst_seed": float(a.min()), "best_seed": float(a.max()),
            })
        # per-seed final-window mean {700,800,900}
        fw = {s: float(np.mean([evals[s][u] for u in FINAL_WINDOW])) for s in SEEDS}
        fwa = np.array(list(fw.values()))
        # AUC over eval grid (trapezoid, normalized by update span)
        pts = np.array([(u, np.mean([evals[s][u] for s in SEEDS])) for u in EVAL_GRID
                        if all(u in evals[s] for s in SEEDS)], dtype=float)
        auc = float(np.trapz(pts[:, 1], pts[:, 0]) / (pts[-1, 0] - pts[0, 0]))
        # first >= 0.9 and first K-consecutive >= 0.9 (per seed, then aggregate)
        first_geo = []
        first_k = []
        for s in SEEDS:
            g = [evals[s][u] for u in EVAL_GRID if u in evals[s]]
            fu = [u for u in EVAL_GRID if u in evals[s]]
            first_geo.append(next((u for u, v in zip(fu, g) if v >= 0.9), None))
            k_ok = None
            for i in range(len(g) - K_CONSEC + 1):
                if all(v >= 0.9 for v in g[i:i + K_CONSEC]):
                    k_ok = fu[i + K_CONSEC - 1]
                    break
            first_k.append(k_ok)
        per_method[m] = {
            "final_window_mean": float(fwa.mean()), "final_window_sd": float(fwa.std(ddof=1)),
            "final_window_per_seed": {str(s): float(v) for s, v in fw.items()},
            "auc": auc, "first_ge_0_9": first_geo, "first_k3_ge_0_9": first_k,
        }
    with (OUT / "gate_prior_training_stability.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(stab_rows[0].keys()))
        w.writeheader(); w.writerows(stab_rows)

    # ---------------- Block 2: gate evolution ----------------
    traj_rows = []          # per method per seed per node: 150-gate stats
    summary_rows = []       # per method per node: cross-seed stats
    seed_consistency = []   # per method per node: cross-seed corr / L2
    for m, base in METHODS.items():
        for s in SEEDS:
            base_dir = base / f"ppo_seed{s}_1m"
            for node in CKPT_NODES:
                ck = base_dir / f"actor_critic_update_{node:04d}.pt"
                if not ck.exists():
                    problems.append(f"{m} seed{s} node{node}: ckpt missing")
                    continue
                logits = extract_gates(load_state(ck))
                agg = aggregate_gates(logits)            # (150,)
                init = initial_gate_vector()             # (150,)
                drift = np.abs(agg - init)
                sat = ((agg < 0.1) | (agg > 0.9)).mean()
                rel_means = [agg[l * 50:(l + 1) * 50].mean() for l in range(3)]
                traj_rows.append({
                    "method": m, "seed": s, "update": node,
                    "mean": float(agg.mean()), "sd": float(agg.std(ddof=1)),
                    "min": float(agg.min()), "max": float(agg.max()),
                    "mean_abs_drift": float(drift.mean()),
                    "saturation_fraction": float(sat),
                    "relation0_mean": rel_means[0], "relation1_mean": rel_means[1],
                    "relation2_mean": rel_means[2],
                    "checkpoint": str(ck),
                })
        # cross-seed at each node (using 150-dim vectors)
        for node in CKPT_NODES:
            vecs = []
            for s in SEEDS:
                ck = base / f"ppo_seed{s}_1m" / f"actor_critic_update_{node:04d}.pt"
                if not ck.exists():
                    vecs = None
                    break
                vecs.append(aggregate_gates(extract_gates(load_state(ck))))
            if vecs is None:
                continue
            V = np.stack(vecs)  # (3,150)
            corrs = [float(np.corrcoef(V[i], V[j])[0, 1]) for i in range(3) for j in range(i + 1, 3)]
            dists = [float(np.linalg.norm(V[i] - V[j])) for i in range(3) for j in range(i + 1, 3)]
            seed_consistency.append({
                "method": m, "update": node,
                "mean_pairwise_pearson": float(np.mean(corrs)),
                "min_pairwise_pearson": float(np.min(corrs)),
                "mean_pairwise_l2": float(np.mean(dists)),
                "cross_seed_sd": float(V.std(axis=0).mean()),
            })
            summary_rows.append({
                "method": m, "update": node,
                "mean_gate": float(V.mean()), "sd_gate": float(V.std(ddof=1)),
                "min_gate": float(V.min()), "max_gate": float(V.max()),
                "saturation_fraction": float(((V < 0.1) | (V > 0.9)).mean()),
            })
    for name, rows in (("gate_prior_gate_trajectory.csv", traj_rows),
                       ("gate_prior_gate_summary.csv", summary_rows),
                       ("gate_prior_seed_consistency.csv", seed_consistency)):
        if not rows:
            problems.append(f"{name}: no rows")
            continue
        with (OUT / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)

    # ---------------- Association (descriptive, n=3) ----------------
    assoc_rows = []
    HO_DIR = {"full": "full_ea_rg", "w_o_gate_prior": "w_o_gate_prior"}
    for m in ("full", "w_o_gate_prior"):
        for s in SEEDS:
            # gate drift: mean |gate_977 - gate_0| over 150 vector
            ck = METHODS[m] / f"ppo_seed{s}_1m" / "actor_critic_update_0977.pt"
            if not ck.exists():
                problems.append(f"{m} seed{s}: final ckpt missing for drift")
                continue
            agg977 = aggregate_gates(extract_gates(load_state(ck)))
            drift = float(np.abs(agg977 - initial_gate_vector()).mean())
            # held-out per-seed recovery (pooled recovery_given_exposure)
            hsum = HELD_OUT_SUM / HO_DIR[m] / f"seed{s}" / "test_checkpoint_summary.csv"
            if not hsum.exists():
                hsum = None
            rec = None
            if hsum is not None:
                exposed = 0.0; recovered = 0.0
                with hsum.open(encoding="utf-8", newline="") as f:
                    for r in csv.DictReader(f):
                        try:
                            exposed += float(r["failure_exposed_count"])
                            recovered += float(r["recovered_given_exposure_count"])
                        except (KeyError, ValueError):
                            continue
                if exposed > 0:
                    rec = recovered / exposed
            assoc_rows.append({
                "method": m, "seed": s, "gate_drift_150": drift,
                "held_out_recovery_pooled": "" if rec is None else f"{rec:.4f}",
            })
    with (OUT / "gate_prior_association.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(assoc_rows[0].keys()))
        w.writeheader(); w.writerows(assoc_rows)

    # ---------------- Figures (exactly 4) ----------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def ev_series(m):
        xs = EVAL_GRID
        arr = np.array([[load_train_log(METHODS[m] / f"ppo_seed{s}_1m" / "train_log.csv").get(u, np.nan)
                         for u in xs] for s in SEEDS], dtype=float)
        return xs, arr

    # fig 1: success curves
    fig, ax = plt.subplots(figsize=(8, 5))
    for m, c in (("full", "#1f77b4"), ("w_o_gate_prior", "#d62728")):
        xs, arr = ev_series(m)
        for i in range(3):
            ax.plot(xs, arr[i], color=c, alpha=0.25, lw=1)
        ax.plot(xs, np.nanmean(arr, axis=0), color=c, lw=2.2,
                label=f"{m} (mean n=3)")
    ax.set_xlabel("update"); ax.set_ylabel("eval success rate")
    ax.set_ylim(0, 1.05); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "fig_success_curves.png", dpi=150); plt.close(fig)

    # fig 2: worst-seed
    fig, ax = plt.subplots(figsize=(8, 5))
    for m, c in (("full", "#1f77b4"), ("w_o_gate_prior", "#d62728")):
        xs, arr = ev_series(m)
        ax.plot(xs, np.nanmin(arr, axis=0), color=c, lw=2.2, label=f"{m} worst-seed")
    ax.set_xlabel("update"); ax.set_ylabel("eval success rate (worst seed)")
    ax.set_ylim(0, 1.05); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "fig_worst_seed.png", dpi=150); plt.close(fig)

    # fig 3: gate evolution (150-vector mean per method, incl. update=0), bilateral
    fig, ax = plt.subplots(figsize=(8, 5))
    nodes = [0] + CKPT_NODES
    for m, c in (("full", "#1f77b4"), ("w_o_gate_prior", "#d62728")):
        v0 = initial_gate_vector() if m == "full" else np.full(150, 0.5)
        means = [v0.mean()]; sds = [v0.std(ddof=1)]
        for node in CKPT_NODES:
            vals = []
            for s in SEEDS:
                ck = METHODS[m] / f"ppo_seed{s}_1m" / f"actor_critic_update_{node:04d}.pt"
                if ck.exists():
                    vals.append(aggregate_gates(extract_gates(load_state(ck))))
            a = np.mean(np.stack(vals), axis=0)
            means.append(float(a.mean())); sds.append(float(a.std(ddof=1)))
        ax.plot(nodes, means, "o-", color=c, lw=2, label=f"{m} mean(150)")
        ax.fill_between(nodes, np.array(means) - np.array(sds),
                        np.array(means) + np.array(sds), alpha=0.15, color=c)
        ax.axhline(0.5987 if m == "full" else 0.5, ls="--", lw=1, color=c, alpha=0.6,
                   label=f"{m} prior init")
    ax.set_xlabel("update"); ax.set_ylabel("sigmoid gate (mean of 150)")
    ax.set_ylim(0.3, 1.0); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "fig_gate_evolution.png", dpi=150)
    plt.close(fig)

    # fig 4: cross-seed dispersion
    fig, ax = plt.subplots(figsize=(8, 5))
    for m, c in (("full", "#1f77b4"), ("w_o_gate_prior", "#d62728")):
        xss = [r["update"] for r in seed_consistency if r["method"] == m]
        l2 = [r["mean_pairwise_l2"] for r in seed_consistency if r["method"] == m]
        ax.plot(xss, l2, "o-", color=c, lw=2, label=f"{m} mean pairwise L2")
    ax.set_xlabel("update"); ax.set_ylabel("cross-seed gate L2 distance")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "fig_cross_seed_dispersion.png", dpi=150)
    plt.close(fig)

    # ---------------- Report ----------------
    lines = [
        "# Gate Prior Mechanism Report (v1.5)",
        "",
        f"- generated: {now}",
        f"- protocol: GATE_PRIOR_MECHANISM_PROTOCOL_V1_5 (+ Addendum A), "
        f"freeze tag gate-prior-mechanism-protocol-freeze-v1.5.0",
        f"- problems: {problems if problems else 'none'}",
        "",
        "## Block 1 — optimization stability (final window {700,800,900}, n=3, ddof=1)",
        "",
        "| method | final-window mean ± SD | AUC | first ≥0.9 (per seed) | first K=3 ≥0.9 (per seed) |",
        "|---|---|---|---|---|",
    ]
    for m in ("full", "w_o_gate_prior"):
        d = per_method[m]
        lines.append(
            f"| {m} | {d['final_window_mean']:.4f} ± {d['final_window_sd']:.4f} | "
            f"{d['auc']:.4f} | {d['first_ge_0_9']} | {d['first_k3_ge_0_9']} |")
    lines += [
        "",
        "## Block 2 — gate evolution (150 aggregated gates; update=0 analytic)",
        "",
        "| method | update | mean | SD | min | max | mean|drift| | sat<0.1/>0.9 | r0/r1/r2 mean | cross-seed pearson | cross-seed L2 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in summary_rows:
        tr = [t for t in traj_rows if t["method"] == r["method"] and t["update"] == r["update"]]
        if not tr:
            continue
        t = tr[0]
        sc = next((x for x in seed_consistency
                   if x["method"] == r["method"] and x["update"] == r["update"]), {})
        lines.append(
            f"| {r['method']} | {r['update']} | {r['mean_gate']:.4f} | {r['sd_gate']:.4f} | "
            f"{r['min_gate']:.3f} | {r['max_gate']:.3f} | {t['mean_abs_drift']:.4f} | "
            f"{r['saturation_fraction']:.3f} | "
            f"{t['relation0_mean']:.3f}/{t['relation1_mean']:.3f}/{t['relation2_mean']:.3f} | "
            f"{sc.get('mean_pairwise_pearson', float('nan')):.3f} | "
            f"{sc.get('mean_pairwise_l2', float('nan')):.2f} |")
    lines += [
        "",
        "## Association (descriptive only, n=3, no significance claims)",
        "",
    ]
    for r in assoc_rows:
        lines.append(
            f"- {r['method']} seed{r['seed']}: gate drift 150 = {r['gate_drift_150']:.4f}, "
            f"held-out recovery (pooled) = {r['held_out_recovery_pooled']}")
    lines += [
        "",
        "## Pre-registered verdict",
        "",
        "Filled by the audit step per protocol Section 7 (SUPPORT / NEUTRAL / COUNTER).",
        "",
        "## Provenance",
        "",
        "- train logs: formal_budget_post_sixth_freeze_v1.4_formal_main_20260802 / "
        "formal_ablation_v1.5_ppo_977_20260804 (locked)",
        "- checkpoints: locked seed-0/1/2 PPO runs, nodes 100..977 (public bilateral nodes)",
        "- held-out per-seed: formal_held_out_v1_5_10800_20260807 (locked)",
    ]
    (OUT / "gate_prior_mechanism_report.md").write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "generated": now,
        "protocol": "GATE_PRIOR_MECHANISM_PROTOCOL_V1_5 (+Addendum A)",
        "eval_grid": EVAL_GRID, "ckpt_nodes": CKPT_NODES,
        "final_window": FINAL_WINDOW, "k_consec": K_CONSEC,
        "n_seeds": len(SEEDS), "gate_channels": 6, "pairs": 25, "hidden": HID,
        "aggregated_gates": 150, "prior_logit": PRIOR_LOGIT,
        "problems": problems,
    }
    (OUT / "gate_prior_analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"OVERALL: {'PASS' if not problems else 'FAIL'}  problems={problems}")
    print(f"output: {OUT}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
