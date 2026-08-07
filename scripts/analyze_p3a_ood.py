# analyze_p3a_ood.py — P3-A.3b statistical analysis (frozen design).
#
# Input: raw episode-level CSV produced by run_p3a_ood_eval.py (8400 rows).
# Outputs per-cell and per-family tables + the primary Full-vs-MAPPO OOD
# early-recovery persistence statistics, plus Gate A/B/C verdict.
#
# Primary endpoint (frozen):
#   RMST80 per (method, seed, cell):
#     integrate min(S(t), tau) over t in [0, tau], S = KM survival
#     (recovery event) estimator with censoring at T_censor.
#   Delta^80_{s,c} = RMST80(Full,s,c) - RMST80(MAPPO,s,c)
#   Delta^OOD_s     = (1/7) sum_c Delta^80_{s,c}
#   mean Delta^OOD  = (1/3) sum_s Delta^OOD_s
#   Delta < 0  -> Full early-recovery better;  Delta > 0 -> MAPPO better.
#
# Secondary per cell: P_rec, conditional E[T_rec | recovered], RMST80, RMST220,
# collision rate. Family aggregates: G1+G2 / M1+M2 / C1+C2 / J1.
#
# Headline MUST be the 7-cell aggregate; never cherry-pick a single cell.
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from scipy import stats

FAMILIES = {
    "Geometry": ["G1", "G2"],
    "Maneuver": ["M1", "M2"],
    "Communication": ["C1", "C2"],
    "Joint": ["J1"],
}
TAU_PRIMARY = 80
TAU_FULL = 220


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def km_rmst(observed: np.ndarray, censored: np.ndarray, tau: float) -> float:
    """RMST via Kaplan-Meier S(t) with right censoring.

    observed[i]  = T_event if the episode recovered (uncensored)
    censored[i]  = T_censor if the episode did NOT recover (censored)
    For recovered episodes, censored value is ignored (event at T_event).
    """
    times = []
    for ev, ce in zip(observed, censored):
        if ev >= 0.0 and ce < 0.0:
            times.append((float(ev), 1.0))
        elif ev < 0.0 and ce >= 0.0:
            times.append((float(ce), 0.0))
        else:
            # both available (should not happen) or both missing: censor at min
            times.append((min(float(ev) if ev >= 0 else np.inf,
                              float(ce) if ce >= 0 else np.inf), 0.0))
    times.sort()
    t_prev = 0.0
    surv = 1.0
    n_risk = len(times)
    area = 0.0
    for t, event in times:
        area += surv * (min(t, tau) - min(t_prev, tau)) if t_prev < tau else 0.0
        if t > tau:
            break
        if event:
            surv *= (n_risk - 1.0) / n_risk
        n_risk -= 1
        t_prev = t
    if t_prev < tau:
        area += surv * (tau - t_prev)
    return float(area)


def bootstrap_rmst_diff(obs_f, cen_f, obs_m, cen_m, tau: float, n_boot: int = 2000,
                        rng: np.random.Generator | None = None) -> tuple[float, float, float, float]:
    """Bootstrap 95% CI for RMST_Full - RMST_MAPPO at tau."""
    if rng is None:
        rng = np.random.default_rng(1208607)
    n_f, n_m = len(obs_f), len(obs_m)
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        i_f = rng.integers(0, n_f, n_f)
        i_m = rng.integers(0, n_m, n_m)
        r_f = km_rmst(obs_f[i_f], cen_f[i_f], tau)
        r_m = km_rmst(obs_m[i_m], cen_m[i_m], tau)
        diffs[b] = r_f - r_m
    lo, hi = np.percentile(diffs, 2.5), np.percentile(diffs, 97.5)
    return float(np.mean(diffs)), float(np.std(diffs)), lo, hi


def cell_stats(rows: list[dict]) -> dict:
    """Secondary per-cell stats for one (method, seed, cell) block."""
    n = len(rows)
    succ = float(np.mean([float(r["success"]) for r in rows]))
    coll = float(np.mean([float(r["collision"]) for r in rows]))
    rec_obs = np.array([float(r["recovery_observed"]) for r in rows])
    p_rec = float(np.mean(rec_obs))
    t_events = np.array([float(r["recovery_event_time"]) for r in rows if float(r["recovery_event_time"]) >= 0])
    t_censors = np.array([float(r["censor_time"]) for r in rows if float(r["censor_time"]) >= 0])
    e_t_rec = float(np.mean(t_events)) if len(t_events) else float("nan")
    rmst80 = km_rmst(t_events, t_censors, TAU_PRIMARY)
    rmst220 = km_rmst(t_events, t_censors, TAU_FULL)
    return {
        "n": n, "success": succ, "collision": coll, "P_rec": p_rec,
        "E_Trec_recovered": e_t_rec, "RMST80": rmst80, "RMST220": rmst220,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="raw episode CSV from P3-A.3a")
    parser.add_argument("--out-md", default="docs/statistics/p3a_ood_results_v1_1/p3a_ood_analysis.md")
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()

    rows = load_rows(Path(args.raw))
    print(f"loaded {len(rows)} rows")

    cells = sorted(set((r["method"], r["train_seed"], r["cell"]) for r in rows))
    per_cell: dict[tuple, dict] = {}
    for m, s, c in cells:
        block = [r for r in rows if (r["method"], r["train_seed"], r["cell"]) == (m, s, c)]
        per_cell[(m, s, c)] = cell_stats(block)

    # --- primary: Full vs MAPPO, per seed, 7-cell aggregate ---
    seed_deltas: dict[str, float] = {}
    rng = np.random.default_rng(1208607)
    lines = ["# P3-A OOD Statistical Analysis (P3-A.3b)",
             "", f"raw: {args.raw}", "", "## Primary: Full vs MAPPO RMST80 (7-cell aggregate)", ""]
    header = ["seed", "cell", "RMST80_Full", "RMST80_MAPPO", "Delta80", "bootstrap_mean", "CI_lo", "CI_hi"]
    table = []
    for s in ["0", "1", "2"]:
        deltas = []
        for c in sorted({cc for (_, _, cc) in cells}):
            st_f = per_cell[("full_ea_rg", s, c)]
            st_m = per_cell[("mappo", s, c)]
            # recompute bootstrap diff from the same raw data
            f_ev = np.array([float(r["recovery_event_time"]) for r in rows
                             if (r["method"], r["train_seed"], r["cell"]) == ("full_ea_rg", s, c) and float(r["recovery_event_time"]) >= 0])
            f_ce = np.array([float(r["censor_time"]) for r in rows
                             if (r["method"], r["train_seed"], r["cell"]) == ("full_ea_rg", s, c) and float(r["censor_time"]) >= 0])
            m_ev = np.array([float(r["recovery_event_time"]) for r in rows
                             if (r["method"], r["train_seed"], r["cell"]) == ("mappo", s, c) and float(r["recovery_event_time"]) >= 0])
            m_ce = np.array([float(r["censor_time"]) for r in rows
                             if (r["method"], r["train_seed"], r["cell"]) == ("mappo", s, c) and float(r["censor_time"]) >= 0])
            mean, sd, lo, hi = bootstrap_rmst_diff(f_ev, f_ce, m_ev, m_ce, TAU_PRIMARY, args.n_boot, rng)
            delta = st_f["RMST80"] - st_m["RMST80"]
            deltas.append(delta)
            table.append([s, c, f"{st_f['RMST80']:.3f}", f"{st_m['RMST80']:.3f}",
                          f"{delta:.3f}", f"{mean:.3f}", f"{lo:.3f}", f"{hi:.3f}"])
        seed_deltas[s] = float(np.mean(deltas))
    table.append(["agg", "7-cell", "", "", f"{np.mean(list(seed_deltas.values())):.3f}", "", "", ""])
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for row in table:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append(f"Delta^OOD per seed: { {s: f'{v:.3f}' for s, v in seed_deltas.items()} }")
    lines.append(f"mean Delta^OOD = {np.mean(list(seed_deltas.values())):.3f}")
    lines.append("")
    lines.append("Interpretation: Delta < 0 -> Full early-recovery better; > 0 -> MAPPO better.")
    lines.append("")

    # --- secondary: per-cell, per-method, seed-averaged ---
    lines.append("## Secondary: seed-averaged per cell (methods)")
    methods = ["full_ea_rg", "mappo", "happo", "param_matched_single"]
    lines.append("| cell | " + " | ".join(methods) + " |")
    lines.append("|" + "|".join(["---"] * (1 + len(methods))) + "|")
    for c in sorted({cc for (_, _, cc) in cells}):
        vals = []
        for m in methods:
            s_r = [per_cell[(m, s, c)] for s in ["0", "1", "2"]]
            vals.append(f"RMST80 {np.mean([v['RMST80'] for v in s_r]):.1f} | "
                        f"P_rec {np.mean([v['P_rec'] for v in s_r]):.2f} | "
                        f"E[T_rec] {np.nanmean([v['E_Trec_recovered'] for v in s_r]):.1f}")
        lines.append(f"| {c} | " + " | ".join(vals) + " |")
    lines.append("")

    # --- family aggregates ---
    lines.append("## Family aggregates (seed-averaged, Full vs MAPPO)")
    for fam, clist in FAMILIES.items():
        vals = []
        for m in ["full_ea_rg", "mappo"]:
            rm = [np.mean([per_cell[(m, s, c)]["RMST80"] for s in ["0", "1", "2"]]) for c in clist]
            vals.append(f"{m}: {np.mean(rm):.2f}")
        lines.append(f"- {fam} ({','.join(clist)}): " + "; ".join(vals))
    lines.append("")

    # --- Gate A/B/C (placeholder logic; final thresholds decided at P3-A.3b freeze) ---
    agg = np.mean(list(seed_deltas.values()))
    sign_ok = all(v < 0 for v in seed_deltas.values())
    lines.append("## Gate (provisional)")
    if agg < 0 and sign_ok:
        gate = "A: early post-failure recovery advantage persists across unseen distribution shifts."
    elif agg < 0:
        gate = "B: advantage persists under selected distribution shifts and is family-dependent."
    else:
        gate = "C: the early-recovery advantage is distribution-dependent."
    lines.append(f"> {gate}")
    lines.append("")

    out = Path(args.out_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
