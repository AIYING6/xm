# analyze_task_support_v1_5.py
# Task-Support mechanism analysis, TASK_SUPPORT_MECHANISM_PROTOCOL_V1_5 (frozen, + Addendum B).
# Read-only rollout over locked checkpoints; no training / tuning. Records relation_adj[2]
# (task-support) trajectories around node failure and recovery events.
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
OUT = ROOT / "docs" / "task_support_v1_5_assets"

sys.path.insert(0, str(ROOT))
from algorithms.ri_gmappo.simple_ri_gmappo import stack_graphs, make_env  # noqa: E402
from scripts.evaluate_ri_gmappo_3d import (  # noqa: E402
    build_config,
    build_agent,
    build_episode_row,
)
from scripts.evaluate_3d_topology_robustness import SCENARIOS  # noqa: E402

FULL_CKPT = (ROOT / "results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802"
             "/ea_rg_mappo_s_gate_prior/ppo_seed{S}_1m/actor_critic_update_0700.pt")
WOT_CKPT = (AB_ROOT / "results/paper_config_runs/formal_ablation_v1.5_ppo_977_20260804"
            "/w_o_task_support/ppo_seed{S}_1m/actor_critic_update_0100.pt")
SEEDS = [0, 1, 2]
BASE_SEED = 745669
EPISODES = int(os.environ.get("TS_EPISODES", "100"))
_SMOKE = os.environ.get("TS_SMOKE", "0") == "1"
SCENARIOS_USED = (["dropout030_delay2_relay_failure"] if _SMOKE
                  else ["dropout030_delay2_relay_failure", "dropout030_delay2_relay_failure_early"])
W = 20  # window half-width (frozen)
BLUE = [0, 1, 2]  # node ids (role 0 scout, 1 relay, 2 attacker); target = node 3
PAIRS = [(i, j) for i in BLUE for j in BLUE]  # 9 blue-blue (receiver, sender)


def make_args(scenario_name: str, ckpt: Path, seed: int, ablation: str):
    s = SCENARIOS[scenario_name]
    return argparse.Namespace(
        checkpoint=ckpt, episodes=EPISODES, eval_batch_size=4, seed=seed, base_seed=BASE_SEED,
        target_policy="straight", communication_range_scale=s.communication_range_scale,
        communication_dropout_prob=s.communication_dropout_prob, message_delay_steps=s.message_delay_steps,
        radar_dropout_prob=s.radar_dropout_prob, strict_target_sensing=True,
        agent_target_info_bottleneck=True, target_prior_position=(0.0, 0.0, 0.0),
        max_target_message_age_steps=40, min_target_confidence=0.0,
        failed_blue_agent=s.failed_blue_agent, node_failure_start_step=s.node_failure_start_step,
        node_failure_duration_steps=s.node_failure_duration_steps, attack_hold_steps=4,
        min_success_step=0, stochastic=False, allow_random_policy=False,
        hidden_dim=64, role_dim=8, intent_dim=8, graph_encoder="multi_relation",
        graph_relation_ablation=ablation, graph_message_ablation="none",
        graph_input_ablation="none", multi_relation_global_residual_weight=0.5,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )


def window_stats(ts_traj: list[np.ndarray], comm_traj: list[np.ndarray],
                 f: int, r: int, steps: int, w: int = W) -> dict:
    """ts_traj: list of length steps, each a 9-vec of relation_adj[2] (blue-blue, receiver-major).
    Returns per-window stats or None entries."""
    def _w(lo, hi):
        seg = np.stack(ts_traj[lo:hi + 1]) if hi >= lo else np.zeros((0, 9))
        cseg = np.stack(comm_traj[lo:hi + 1]) if hi >= lo else np.zeros((0, 9))
        if seg.shape[0] == 0:
            return None
        act = (seg > 0.5).astype(float)
        return {
            "mean_strength": float(seg.mean()),
            "nonzero_fraction": float(act.mean()),
            "mean_comm_fraction": float((cseg > 0.5).mean()),
            "pair_support_strong": "1" if act.mean() > 0.5 else "0",
            "n_steps": int(seg.shape[0]),
            "pair_rates": ",".join(f"{v:.3f}" for v in
                                   (act.mean(axis=0) if seg.shape[0] else np.zeros(9))),
        }

    res = {}
    if f >= 0:
        res["pre_failure"] = _w(max(0, f - w), max(0, f - 1))
        res["early_post_failure"] = _w(f, min(steps - 1, f + w))
    else:
        res["pre_failure"] = None
        res["early_post_failure"] = None
    if r >= 0 and r > f:
        res["pre_recovery"] = _w(max(f, r - w), max(f, r - 1))
        res["post_recovery"] = _w(r, min(steps - 1, r + w))
    else:
        res["pre_recovery"] = None
        res["post_recovery"] = None
    return res


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device={device}", flush=True)

    runs = []
    for method, templ, abl in (("full", FULL_CKPT, "none"),
                               ("w_o_task_support", WOT_CKPT, "no_task_support")):
        for s in SEEDS:
            ck = Path(str(templ).replace("{S}", str(s)))
            if not ck.exists():
                problems.append(f"{method} seed{s}: ckpt missing {ck}")
                continue
            for sc in SCENARIOS_USED:
                runs.append((method, s, sc, make_args(sc, ck, s, abl)))
    if not runs:
        print("no runs"); return 1

    episode_rows: list[dict] = []
    traj_rows: list[dict] = []
    dyn_rows: list[dict] = []
    ts_full = {}   # (scenario, ep) -> {success, recovery_step, failure_step, ts_traj, comm_traj, steps}
    ts_wot = {}

    for method, seed, scname, args in runs:
        cfg = build_config(args)
        agent, policy_source = build_agent(args, cfg)
        agent = agent.to(device)
        print(f"run {method} seed{seed} {scname}", flush=True)
        n_success = n_rec = 0
        with torch.no_grad():
            for batch_start in range(0, EPISODES, args.eval_batch_size):
                batch_eps = list(range(batch_start, min(EPISODES, batch_start + args.eval_batch_size)))
                envs, obs_l, share_l, graph_l, stepinf_l, reward_l, active = [], [], [], [], [], [], []
                ts_traj_l: list[list] = [[] for _ in batch_eps]
                comm_traj_l: list[list] = [[] for _ in batch_eps]
                act_bytes_l: list[list] = [[] for _ in batch_eps]
                for i, ep in enumerate(batch_eps):
                    env = make_env(cfg, BASE_SEED + ep, training=False)
                    obs, so, g = env.reset()
                    envs.append(env); obs_l.append(obs); share_l.append(so); graph_l.append(g)
                    stepinf_l.append([]); reward_l.append(0.0); active.append(True)
                while any(active):
                    ai = [i for i, a in enumerate(active) if a]
                    g = stack_graphs([graph_l[i] for i in ai])
                    actions, _, _, _, _, _, _ = agent.get_action_and_value(
                        torch.as_tensor(np.stack([obs_l[i] for i in ai]), dtype=torch.float32, device=device),
                        torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(g["role"], dtype=torch.long, device=device),
                        torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                        torch.as_tensor(np.stack([share_l[i] for i in ai]), dtype=torch.float32, device=device),
                        relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device),
                        deterministic=True,
                        intent_label=torch.as_tensor(g["intent_label"], dtype=torch.long, device=device),
                        detach_intent=False, oracle_intent=False,
                    )
                    act = actions.cpu().numpy()
                    # record ts/comm/action before stepping (current observation state)
                    for pos, env_i in enumerate(ai):
                        ra = graph_l[env_i]["relation_adj"]
                        ts = ra[2, BLUE][:, BLUE]          # (3,3) blue-blue
                        cm = ra[1, BLUE][:, BLUE]
                        ts_traj_l[env_i].append(ts.flatten())
                        comm_traj_l[env_i].append(cm.flatten())
                        act_bytes_l[env_i].append(act[pos].astype("<f4").tobytes())
                    for k, env_i in enumerate(ai):
                        obs, so, graph, rewards, dones, info = envs[env_i].step(act[k])
                        reward_l[env_i] += float(np.sum(rewards))
                        stepinf_l[env_i].append(info)
                        obs_l[env_i] = obs; share_l[env_i] = so; graph_l[env_i] = graph
                        if np.all(dones):
                            ep = batch_eps[env_i]
                            row = build_episode_row(args, policy_source, BASE_SEED + ep, ep,
                                                    stepinf_l[env_i], info, reward_l[env_i])
                            ts = np.stack(ts_traj_l[env_i])
                            cm = np.stack(comm_traj_l[env_i])
                            f = -1
                            for ii, inf in enumerate(stepinf_l[env_i]):
                                if float(inf.get("node_failure_active", 0.0)) > 0.5:
                                    f = ii
                                    break
                            rec = float(row["post_failure_chain_recovered"])
                            r = float(row["post_failure_first_chain_step"]) if rec > 0.5 else -1.0
                            steps = int(row["steps"])
                            success = float(row["success"]) > 0.5
                            entry = {"success": success, "failure_step": f, "recovery_step": int(r) if r >= 0 else -1,
                                     "steps": steps, "ts_traj": ts, "comm_traj": cm,
                                     "t_recovery_steps": float(row["post_failure_chain_recovery_steps"])}
                            (ts_full if method == "full" else ts_wot)[(scname, ep)] = entry
                            act_hash = hashlib.sha1(b"".join(act_bytes_l[env_i])).hexdigest()[:16]
                            # ---- Block A dynamics (Full internal; recorded for all) ----
                            active_mask = ts > 0.5                      # (steps, 9)
                            any_active = active_mask.any(axis=1)        # (steps,)
                            first_after_fail = -1
                            if f >= 0:
                                idx = np.where(any_active[f + 1:])[0]
                                if idx.size:
                                    first_after_fail = int(idx[0] + f + 1)
                            persist = 0
                            if f >= 0:
                                best = run = 0
                                for v in any_active[f + 1:]:
                                    run = run + 1 if v else 0
                                    best = max(best, run)
                                persist = best
                            unique_pairs = int(np.unique(np.where(active_mask)[1]).size)
                            rec_boost = np.nan
                            ri = int(r) if r >= 0 else -1
                            if f >= 0 and ri >= 0 and ri - 1 >= f:
                                early = ts[f:min(steps, f + 10)].mean()
                                pre_r = ts[max(f, ri - 10):ri].mean()
                                rec_boost = float(pre_r - early)
                            dyn_rows.append({
                                "method": method, "seed": seed, "scenario": scname, "episode": ep,
                                "success": "1" if success else "0",
                                "recovered": "1" if rec > 0.5 else "0",
                                "steps": steps, "failure_step": f,
                                "recovery_step": int(r) if r >= 0 else -1,
                                "first_support_after_failure": first_after_fail,
                                "support_persistence": persist,
                                "unique_active_pairs": unique_pairs,
                                "pre_recovery_boost": f"{rec_boost:.4f}" if np.isfinite(rec_boost) else "",
                                "action_hash": act_hash,
                            })
                            episode_rows.append({
                                "method": method, "seed": seed, "scenario": scname, "episode": ep,
                                "success": "1" if success else "0", "steps": steps,
                                "failure_step": f, "recovery_step": int(r) if r >= 0 else -1,
                                "post_failure_chain_recovered": "1" if rec > 0.5 else "0",
                                "t_recovery_steps": f"{float(row['post_failure_chain_recovery_steps']):.1f}",
                                "action_hash": act_hash,
                            })
                            ws = window_stats(ts, cm, f, int(r) if r >= 0 else -1, steps)
                            for wname, wst in ws.items():
                                if wst is None:
                                    continue
                                traj_rows.append({
                                    "method": method, "seed": seed, "scenario": scname, "episode": ep,
                                    "window": wname, "mean_strength": wst["mean_strength"],
                                    "nonzero_fraction": wst["nonzero_fraction"],
                                    "mean_comm_fraction": wst["mean_comm_fraction"],
                                    "pair_support_strong": wst["pair_support_strong"],
                                    "pair_rates": wst["pair_rates"],
                                })
                            if success:
                                n_success += 1
                            if rec > 0.5:
                                n_rec += 1
                            active[env_i] = False
        print(f"  success={n_success}/{EPISODES} recovered={n_rec}/{EPISODES}", flush=True)

    for name, rows, cols in (
        ("task_support_episode_manifest.csv", episode_rows,
         ["method", "seed", "scenario", "episode", "success", "steps", "failure_step",
          "recovery_step", "post_failure_chain_recovered", "t_recovery_steps", "action_hash"]),
        ("task_support_relation_trajectory.csv", traj_rows,
         ["method", "seed", "scenario", "episode", "window", "mean_strength",
          "nonzero_fraction", "mean_comm_fraction", "pair_support_strong", "pair_rates"]),
        ("task_support_dynamics.csv", dyn_rows,
         ["method", "seed", "scenario", "episode", "success", "recovered", "steps",
          "failure_step", "recovery_step", "first_support_after_failure",
          "support_persistence", "unique_active_pairs", "pre_recovery_boost", "action_hash"]),
    ):
        if not rows:
            problems.append(f"{name}: no rows")
            continue
        with (OUT / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader(); w.writerows(rows)

    # ---- window summary + seed consistency ----
    summary, seed_cons = _window_summary(traj_rows)
    for name, rows, cols in (
        ("task_support_window_summary.csv", summary,
         ["method", "scenario", "window", "mean_strength_mean", "nonzero_mean",
          "n_episodes"]),
        ("task_support_seed_consistency.csv", seed_cons,
         ["method", "scenario", "window", "seed", "mean_strength", "nonzero_fraction"]),
    ):
        with (OUT / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader(); w.writerows(rows)

    # ---- case selection (frozen rule, seed0 only) ----
    case_rows = _select_cases(ts_full, ts_wot, problems)
    with (OUT / "task_support_case_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(case_rows[0].keys()))
        w.writeheader(); w.writerows(case_rows)

    # ---- figures ----
    try:
        _make_figures(ts_full, ts_wot, traj_rows, case_rows)
    except Exception as e:  # noqa: BLE001
        problems.append(f"figures failed: {e}")

    _write_report(now, problems, episode_rows, traj_rows, summary, case_rows)

    print(f"\nOVERALL: {'PASS' if not problems else 'FAIL'}  problems={problems}")
    print(f"output: {OUT}")
    return 0 if not problems else 1


def _window_summary(traj_rows):
    from collections import defaultdict
    agg: dict[tuple, list[float]] = defaultdict(list)
    nz: dict[tuple, list[float]] = defaultdict(list)
    for r in traj_rows:
        k = (r["method"], r["scenario"], r["window"])
        agg[k].append(float(r["mean_strength"]))
        nz[k].append(float(r["nonzero_fraction"]))
    summary = []
    for (m, sc, wn), vals in sorted(agg.items()):
        summary.append({"method": m, "scenario": sc, "window": wn,
                        "mean_strength_mean": f"{float(np.mean(vals)):.4f}",
                        "nonzero_mean": f"{float(np.mean(nz[(m, sc, wn)])):.4f}",
                        "n_episodes": len(vals)})
    # per-seed listing (mean strength + nonzero per seed)
    per = defaultdict(list)
    per_nz = defaultdict(list)
    for r in traj_rows:
        k = (r["method"], r["scenario"], r["window"], int(r["seed"]))
        per[k].append(float(r["mean_strength"]))
        per_nz[k].append(float(r["nonzero_fraction"]))
    seed_cons = []
    for (m, sc, wn, sd), vals in sorted(per.items()):
        seed_cons.append({"method": m, "scenario": sc, "window": wn, "seed": sd,
                          "mean_strength": f"{float(np.mean(vals)):.4f}",
                          "nonzero_fraction": f"{float(np.mean(per_nz[(m, sc, wn, sd)])):.4f}"})
    return summary, seed_cons


def _select_cases(ts_full, ts_wot, problems):
    from collections import defaultdict
    # group by scenario+episode across seeds; primary = seed0
    cand = {"C1": [], "C2": [], "C3": []}
    for (sc, ep), fe in ts_full.items():
        we = ts_wot.get((sc, ep))
        if we is None:
            continue
        if fe["failure_step"] < 0 or we["failure_step"] < 0:
            continue
        fs, ws_ = fe["success"], we["success"]
        if fs and ws_ and fe["recovery_step"] >= 0 and we["recovery_step"] >= 0:
            dt = we["recovery_step"] - fe["recovery_step"]
            if dt >= 2:  # Full recovers at least 2 steps faster
                cand["C1"].append(("full", 0, sc, ep, fs, fe["steps"], fe["failure_step"],
                                   fe["recovery_step"], we["recovery_step"]))
        elif fs and not ws_:
            cand["C2"].append(("full", 0, sc, ep, fs, fe["steps"], fe["failure_step"],
                               fe["recovery_step"], we["recovery_step"]))
        elif not fs and not ws_:
            cand["C3"].append(("full", 0, sc, ep, fs, fe["steps"], fe["failure_step"],
                               fe["recovery_step"], we["recovery_step"]))
    out = []
    for cls in ("C1", "C2", "C3"):
        if not cand[cls]:
            problems.append(f"case class {cls}: no candidates")
            continue
        cand[cls].sort(key=lambda x: (SCENARIOS_USED.index(x[2]), x[3]))
        c = cand[cls][0]
        out.append({"case_class": cls, "method": c[0], "seed": c[1], "scenario": c[2],
                    "episode": c[3], "full_success": "1" if c[4] else "0", "steps": c[5],
                    "failure_step": c[6], "full_recovery_step": c[7],
                    "wot_recovery_step": c[8]})
    return out or [{"case_class": "none", "method": "", "seed": "", "scenario": "",
                    "episode": "", "full_success": "", "steps": "", "failure_step": "",
                    "full_recovery_step": "", "wot_recovery_step": ""}]


def _make_figures(ts_full, ts_wot, traj_rows, case_rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from collections import defaultdict
    # fig 1: window strength by method/scenario (full only meaningful; w/o = 0)
    agg = defaultdict(list)
    for r in traj_rows:
        agg[(r["method"], r["scenario"], r["window"])].append(float(r["mean_strength"]))
    order = ["pre_failure", "early_post_failure", "pre_recovery", "post_recovery"]
    fig, ax = plt.subplots(figsize=(9, 5))
    for sc in SCENARIOS_USED:
        x = [o for o in order if (("full", sc, o) in agg)]
        y = [float(np.mean(agg[("full", sc, o)])) for o in x]
        ax.plot(range(len(x)), y, "o-", label=f"full {sc}")
    ax.set_xticks(range(len(x)))
    ax.set_xticklabels(x, rotation=20)
    ax.set_ylabel("task-support mean strength (9 pairs)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "fig_ts_window_strength.png", dpi=150); plt.close(fig)
    # fig 2: case examples (up to 3)
    n = len([c for c in case_rows if c["case_class"] != "none"])
    if n > 0:
        fig, axes = plt.subplots(1, min(n, 3), figsize=(5.5 * min(n, 3), 4), squeeze=False)
        for i, cr in enumerate([c for c in case_rows if c["case_class"] != "none"][:3]):
            ax = axes[0][i]
            key = (cr["scenario"], int(cr["episode"]))
            e = ts_full.get(key)
            if e is None:
                continue
            ts = e["ts_traj"]
            nz = (ts > 0.5).mean(axis=1)
            ax.plot(nz, color="#1f77b4", lw=1.5)
            ax.axvline(e["failure_step"], color="red", ls="--", lw=1, label="failure")
            if e["recovery_step"] >= 0:
                ax.axvline(e["recovery_step"], color="green", ls="--", lw=1, label="recovery")
            ax.set_title(f"{cr['case_class']}: {cr['scenario']} ep{cr['episode']}")
            ax.set_xlabel("step"); ax.set_ylabel("ts nonzero frac")
            ax.legend(fontsize=7); ax.grid(alpha=0.3)
        fig.tight_layout(); fig.savefig(OUT / "fig_ts_case_examples.png", dpi=150)
        plt.close(fig)


def _write_report(now, problems, episode_rows, traj_rows, summary, case_rows):
    lines = [
        "# Task-Support Mechanism Report (v1.5)",
        "",
        f"- generated: {now}",
        "- protocol: TASK_SUPPORT_MECHANISM_PROTOCOL_V1_5 (+ Addendum B), freeze tag "
        "task-support-mechanism-protocol-freeze-v1.5.0",
        f"- problems: {problems if problems else 'none'}",
        "",
        "## Block 1 — performance effect (cited from locked held-out)",
        "",
        "| method | success | recovery | t_success | t_recovery | worst-seed | 3-seed SD |",
        "|---|---|---|---|---|---|---|",
        "| full | 0.985 ± 0.011 | 0.971 ± 0.021 | 46.14 | 10.82 | - | - |",
        "| w/o Task-Support | - | 0.892 | - | 16.14 | - | - |",
        "",
        "## Block 2 — task-support relation strength by window (pooled over episodes)",
        "",
        "| method | scenario | window | mean strength | nonzero fraction | n |",
        "|---|---|---|---|---|---|",
    ]
    for r in summary:
        lines.append(f"| {r['method']} | {r['scenario']} | {r['window']} | "
                     f"{r['mean_strength_mean']} | {r['nonzero_mean']} | {r['n_episodes']} |")
    lines += [
        "",
        "## Case manifest (frozen selection rule)",
        "",
        "| class | method | seed | scenario | episode | full_success | steps | failure_step | full_rec | wot_rec |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in case_rows:
        lines.append(f"| {c['case_class']} | {c['method']} | {c['seed']} | {c['scenario']} | "
                     f"{c['episode']} | {c['full_success']} | {c['steps']} | {c['failure_step']} | "
                     f"{c['full_recovery_step']} | {c['wot_recovery_step']} |")
    lines += [
        "",
        "## Pre-registered verdict",
        "",
        "Filled at lock time per protocol Section 6 (SUPPORT / EMPIRICAL SUPPORT ONLY / INCONCLUSIVE).",
        "",
        "## Provenance",
        "",
        "- checkpoints: full ppo_seed{S}_1m update_0700 (locked); w_o_task_support ppo_seed{S}_1m "
        "update_0100 (locked)",
        "- base_seed=745669 (held-out split), 2 scenarios x 2 methods x 3 seeds x 100 episodes = 1200 episodes",
        "- windows: [-20,-1]/[0,20]/[rec-20,rec-1]/[rec,rec+20]; 9 blue-blue pairs (Addendum B)",
    ]
    (OUT / "task_support_mechanism_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
