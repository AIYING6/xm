# run_survival_v1_1.py — local execution of Survival Protocol v1.1 on locked held-out data.
# Population = Early + Nominal scenarios (method x seed x scenario = 100 exposed each).
# t=0 = node_failure_start_step; T = stable_window_start - start (recovered);
# censored C = steps - start. tau_primary = 220.
# Outputs docs/statistics/survival_results_v1_1/
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

BASE = Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/formal_held_out_v1_5_10800_20260807/held_out_v1.5")
OUT = Path(r"D:/Code/Codex/ri_gmappo_uav/docs/statistics/survival_results_v1_1")
METHODS = ["full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
           "no_graph", "single_graph", "param_matched_single", "happo", "mappo"]
LABEL = {"full_ea_rg": "EA-RG Full", "w_o_gate_prior": "w/o Gate Prior",
         "w_o_task_support": "w/o Task-Support", "w_o_role_pair_gate": "w/o Role-Pair Mod",
         "no_graph": "No Graph", "single_graph": "Single Graph",
         "param_matched_single": "Wider Single-Graph", "happo": "HAPPO", "mappo": "MAPPO"}
PRIMARY_SC = ["dropout030_delay2_relay_failure_early", "dropout030_delay2_relay_failure"]
ALL_SC = PRIMARY_SC + ["dropout030_delay2_relay_failure_delayed", "dropout030_delay2_relay_failure_late"]
SEEDS = ["0", "1", "2"]
HOLD = 4
TAU = 220
SENS = [50, 80, 100, 150, 190, 220]


def load(m, s):
    rows = list(csv.DictReader((BASE / m / f"seed{s}" / "test_episode_metrics.csv").open(encoding="utf-8")))
    out = {}
    for r in rows:
        sc = r["scenario"]
        fs = int(float(r["node_failure_start_step"]))
        steps = int(float(r["steps"]))
        exposed = steps >= fs
        rec = float(r["post_failure_chain_recovered"]) > 0.5
        if rec:
            T = float(r["post_failure_chain_recovery_steps"])
            d = 1
        else:
            T = float(steps - fs)
            d = 0
        out.setdefault(sc, []).append((exposed, T, d))
    return out


def km_rmst(times, events, tau):
    """Discrete KM + RMST(tau). times/events arrays; RMST = sum_{t=0}^{tau-1} S(t)."""
    times = np.asarray(times, float)
    events = np.asarray(events, float)
    n = len(times)
    order = np.argsort(times)
    times = times[order]; events = events[order]
    S = 1.0
    rmst = 0.0
    t_prev = 0.0
    n_at_risk = n
    i = 0
    while t_prev < tau:
        t_next = times[i] if i < n else tau
        if t_next > t_prev:
            seg = min(t_next, tau) - t_prev
            rmst += S * seg
            t_prev = t_next
        if i >= n:
            break
        # process events at t_next
        d_at = 0
        c_at = 0
        while i < n and times[i] == t_next:
            if events[i]:
                d_at += 1
            else:
                c_at += 1
            i += 1
        n_at_risk -= c_at
        if n_at_risk > 0:
            S *= (1 - d_at / n_at_risk)
        n_at_risk -= d_at
        if n_at_risk <= 0:
            break
    return rmst, S


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # per (method, seed): survival samples from primary scenarios
    surv = {}
    for m in METHODS:
        for s in SEEDS:
            d = load(m, s)
            T = []
            E = []
            for sc in PRIMARY_SC:
                for exposed, t, e in d.get(sc, []):
                    if not exposed:
                        continue
                    T.append(t); E.append(e)
            surv[(m, s)] = (np.array(T), np.array(E))

    # ---- RMST per (method, seed) at tau_primary ----
    rmst = {}
    for m in METHODS:
        rmst[m] = {}
        for s in SEEDS:
            T, E = surv[(m, s)]
            rmst[m][s], _ = km_rmst(T, E, TAU)

    with (OUT / "rmst_seedwise.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["method", "seed", "rmst_tau220", "n_exposed"])
        for m in METHODS:
            for s in SEEDS:
                w.writerow([m, s, f"{rmst[m][s]:.4f}", len(surv[(m, s)][0])])

    # ---- summary: mean +/- SD + per-seed delta vs Full ----
    summ = []
    full = {s: rmst["full_ea_rg"][s] for s in SEEDS}
    with (OUT / "rmst_summary.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["method", "rmst_mean", "rmst_sd", "d_seed0", "d_seed1", "d_seed2", "d_mean"])
        for m in METHODS:
            vals = np.array([rmst[m][s] for s in SEEDS])
            ds = [full[s] - rmst[m][s] for s in SEEDS]
            w.writerow([m, f"{vals.mean():.4f}", f"{vals.std(ddof=1):.4f}",
                        f"{ds[0]:+.4f}", f"{ds[1]:+.4f}", f"{ds[2]:+.4f}", f"{np.mean(ds):+.4f}"])
            summ.append((m, vals.mean(), vals.std(ddof=1), ds))

    # ---- sensitivity RMST ----
    with (OUT / "sensitivity_rmst.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tau"] + [LABEL[m] for m in METHODS])
        for tau in SENS:
            row = [tau]
            for m in METHODS:
                vals = np.array([km_rmst(*surv[(m, s)], tau)[0] for s in SEEDS])
                row.append(f"{vals.mean():.2f}")
            w.writerow(row)

    # ---- hierarchical paired bootstrap (B=10000, rng=20260807) ----
    rng = np.random.default_rng(20260807)
    B = 10000
    comparators = ["mappo", "happo", "param_matched_single", "w_o_role_pair_gate",
                   "single_graph", "no_graph", "w_o_gate_prior", "w_o_task_support"]
    bs = {}
    for comp in comparators:
        bs[comp] = {tau: [] for tau in SENS}
    n_ep = 200  # 2 scenarios x 100
    for _ in range(B):
        seeds = rng.integers(0, 3, size=3)
        for comp in comparators:
            d_full = []
            d_comp = []
            for s in seeds:
                idx = rng.integers(0, n_ep, size=n_ep)
                Tf, Ef = surv[("full_ea_rg", str(s))]
                Tc, Ec = surv[(comp, str(s))]
                d_full.append((Tf[idx], Ef[idx]))
                d_comp.append((Tc[idx], Ec[idx]))
            Tf = np.concatenate([x[0] for x in d_full]); Ef = np.concatenate([x[1] for x in d_full])
            Tc = np.concatenate([x[0] for x in d_comp]); Ec = np.concatenate([x[1] for x in d_comp])
            for tau in SENS:
                rF, _ = km_rmst(Tf, Ef, tau)
                rC, _ = km_rmst(Tc, Ec, tau)
                bs[comp][tau].append(rF - rC)
    with (OUT / "hierarchical_bootstrap.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["comparison", "tau", "observed_delta", "ci_low", "ci_high", "p_delta_lt_0"])
        for comp in comparators:
            obs = [full[s] - rmst[comp][s] for s in SEEDS]
            obs_mean = np.mean(obs)
            for tau in SENS:
                a = np.array(bs[comp][tau])
                lo, hi = np.percentile(a, [2.5, 97.5])
                p = float((a < 0).mean())
                w.writerow([LABEL[comp], tau, f"{obs_mean:.3f}", f"{lo:.3f}", f"{hi:.3f}", f"{p:.4f}"])

    # ---- KM curves (pooled over seeds, primary) ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    def km_step(T, E):
        order = np.argsort(T); ts = T[order]; es = E[order]
        u = np.unique(ts)
        S = []
        n_at_risk = len(T)
        i = 0
        for t in u:
            d = 0
            while i < len(ts) and ts[i] == t:
                d += es[i]; i += 1
            S.append(1 - d / n_at_risk)
            n_at_risk -= d
        S = np.cumprod(S)
        return u, S

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for m in METHODS:
        T = np.concatenate([surv[(m, s)][0] for s in SEEDS])
        E = np.concatenate([surv[(m, s)][1] for s in SEEDS])
        u, S = km_step(T, E)
        ax.step(u, S, where="post", label=LABEL[m])
    ax.set_xlim(0, TAU); ax.set_ylim(0, 1.05)
    ax.set_xlabel("steps after failure onset (t)"); ax.set_ylabel("S(t) = P(T>t)")
    ax.set_title("Pooled KM of post-failure recovery (primary: Early+Nominal, n=600/method)")
    ax.legend(fontsize=7, ncol=2); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "km_recovery_curve_primary.png", dpi=150)
    plt.close(fig)

    # per-seed KM for Full vs MAPPO
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for m, c in (("full_ea_rg", "#1f77b4"), ("mappo", "#d62728")):
        for s in SEEDS:
            u, S = km_step(*surv[(m, s)])
            ax.step(u, S, where="post", color=c, alpha=0.45, lw=1)
    ax.set_xlim(0, TAU); ax.set_ylim(0, 1.05)
    ax.set_xlabel("steps after failure onset"); ax.set_ylabel("S(t)")
    ax.set_title("Per-seed KM: Full (blue) vs MAPPO (red)")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "km_recovery_curve_primary_per_seed.png", dpi=150)
    plt.close(fig)

    # ---- report ----
    lines = ["# Survival Analysis v1.1 — local execution (locked held-out)", "",
             "## Primary RMST(220) mean ± SD (per-seed; n=3)",
             "", "| method | RMST(220) | Full − method (seed0/1/2) |", "|---|---|---|"]
    for m, mu, sd, ds in summ:
        lines.append(f"| {LABEL[m]} | {mu:.2f} ± {sd:.2f} | "
                     f"{ds[0]:+.2f} / {ds[1]:+.2f} / {ds[2]:+.2f} |")
    lines += ["", "## Sensitivity RMST (mean over seeds)", "",
              "| tau | " + " | ".join(LABEL[m] for m in METHODS) + " |",
              "|---|---|"]
    for tau in SENS:
        row = [str(tau)]
        for m in METHODS:
            vals = np.array([km_rmst(*surv[(m, s)], tau)[0] for s in SEEDS])
            row.append(f"{vals.mean():.2f}")
        lines.append("| " + " | ".join(row) + " |")
    (OUT / "survival_report_v1_1.md").write_text("\n".join(lines), encoding="utf-8")
    print("survival v1.1 done; outputs in", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
