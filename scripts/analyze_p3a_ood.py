# analyze_p3a_ood.py — P3-A.3b statistical analysis (frozen design, protocol v1.0 §8).
#
# Input: raw episode-level CSV produced by run_p3a_ood_eval.py (8400 rows, locked
# at p3a-ood-raw-results-lock-v1.0).
#
# Primary endpoint (frozen):
#   RMST80 per (method, seed, cell):
#     integrate min(S(t), tau) over t in [0, tau], S = KM survival (recovery
#     event) estimator with right censoring at T_censor.
#   Delta^80_{s,c} = RMST80(Full,s,c) - RMST80(MAPPO,s,c)
#   Delta^OOD_s     = (1/7) sum_c Delta^80_{s,c}
#   mean Delta^OOD  = (1/3) sum_s Delta^OOD_s
#   Delta < 0 -> Full early-recovery better; Delta > 0 -> MAPPO better.
#
# Uncertainty (frozen): hierarchical paired bootstrap — resample seeds, then
# episodes within each seed x cell using the SAME episode index for Full and
# MAPPO (matched), B = 10,000, RNG seed = 20260807. Report 95% CI and
# P(Delta < 0).
#
# Secondary per cell: P_rec, conditional E[T_rec | recovered], RMST80, RMST220,
# collision. Family aggregates: G1+G2 / M1+M2 / C1+C2 / J1.
# HAPPO and Wider-SG are strong-reference comparators only.
#
# Headline MUST be the 7-cell aggregate; never cherry-pick a single cell.
# After the first output, no re-tuning of tau/cells/checkpoints/weights/recovery
# definition is allowed. A genuine code bug -> STOP, keep first output, write
# invalidation memo, fix + version bump; never silently re-run.
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

FAMILIES = {
    "Geometry": ["G1", "G2"],
    "Maneuver": ["M1", "M2"],
    "Communication": ["C1", "C2"],
    "Joint": ["J1"],
}
CELLS_ORDER = ["C1", "C2", "G1", "G2", "J1", "M1", "M2"]
SEEDS = ["0", "1", "2"]
TAU_PRIMARY = 80
TAU_FULL = 220
N_BOOT = 10000
RNG_SEED = 20260807
FULL_NAME = "full_ea_rg"
MAPPO_NAME = "mappo"


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def km_rmst(observed: np.ndarray, censored: np.ndarray, tau: float) -> float:
    """RMST via Kaplan-Meier S(t) with right censoring.

    observed[i] = T_event if the episode recovered (uncensored); else -1.
    censored[i] = T_censor if the episode did NOT recover; else -1.

    RMST(tau) = integral_0^tau S(t) dt. Because S(t) <= 1, RMST must lie in
    [0, tau]; any value outside that interval indicates an integration bug.
    """
    times = []
    for ev, ce in zip(observed, censored):
        if ev >= 0.0 and ce < 0.0:
            times.append((float(ev), 1.0))
        elif ev < 0.0 and ce >= 0.0:
            times.append((float(ce), 0.0))
        else:
            times.append((min(float(ev) if ev >= 0 else np.inf,
                              float(ce) if ce >= 0 else np.inf), 0.0))
    times.sort()
    t_prev = 0.0
    surv = 1.0
    n_risk = len(times)
    area = 0.0
    for t, event in times:
        if t_prev >= tau:
            break
        upper = min(t, tau)
        area += surv * (upper - t_prev)
        t_prev = upper
        if t >= tau:
            break
        if event:
            surv *= (n_risk - 1.0) / n_risk
        n_risk -= 1
    # Trailing segment only if we did not already reach tau in the loop above.
    if t_prev < tau:
        area += surv * (tau - t_prev)
    return float(area)


def block_times(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Extract (event_times, censor_times) for one (method, seed, cell) block."""
    ev = np.array([float(r["recovery_event_time"]) for r in rows], dtype=float)
    ce = np.array([float(r["censor_time"]) for r in rows], dtype=float)
    return ev, ce


def hierarchical_bootstrap_delta(
    rows: list[dict],
    n_boot: int = N_BOOT,
    rng_seed: int = RNG_SEED,
) -> tuple[float, float, float, float, float]:
    """Hierarchical paired bootstrap of mean Delta^OOD.

    Level 1: resample 3 training seeds with replacement.
    Level 2: within each drawn seed x cell, resample episodes with replacement
             using the SAME index for Full and MAPPO (matched pairing).
    Returns (mean_delta, sd_delta, ci_lo, ci_hi, p_delta_lt_0).
    """
    rng = np.random.default_rng(rng_seed)
    # pre-group by (seed, cell)
    grouped: dict[tuple[str, str], tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for seed in SEEDS:
        for cell in CELLS_ORDER:
            f = [r for r in rows if r["method"] == FULL_NAME and r["train_seed"] == seed and r["cell"] == cell]
            m = [r for r in rows if r["method"] == MAPPO_NAME and r["train_seed"] == seed and r["cell"] == cell]
            f_ev, f_ce = block_times(f)
            m_ev, m_ce = block_times(m)
            grouped[(seed, cell)] = (f_ev, f_ce, m_ev, m_ce)

    n_eps = 100
    deltas = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        drawn_seeds = rng.choice(SEEDS, size=3, replace=True)
        seed_aggs = []
        for seed in drawn_seeds:
            cell_deltas = []
            for cell in CELLS_ORDER:
                f_ev, f_ce, m_ev, m_ce = grouped[(seed, cell)]
                idx = rng.integers(0, n_eps, size=n_eps)
                rmst_f = km_rmst(f_ev[idx], f_ce[idx], TAU_PRIMARY)
                rmst_m = km_rmst(m_ev[idx], m_ce[idx], TAU_PRIMARY)
                cell_deltas.append(rmst_f - rmst_m)
            seed_aggs.append(float(np.mean(cell_deltas)))
        deltas[b] = float(np.mean(seed_aggs))

    mean_d = float(np.mean(deltas))
    sd_d = float(np.std(deltas, ddof=1))
    lo, hi = float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))
    p_lt0 = float(np.mean(deltas < 0))
    return mean_d, sd_d, lo, hi, p_lt0


def cell_stats(rows: list[dict]) -> dict:
    n = len(rows)
    succ = float(np.mean([float(r["success"]) for r in rows]))
    coll = float(np.mean([float(r["collision"]) for r in rows]))
    rec = np.array([float(r["recovery_observed"]) for r in rows])
    p_rec = float(np.mean(rec))
    t_events = np.array([float(r["recovery_event_time"]) for r in rows if float(r["recovery_event_time"]) >= 0])
    t_censors = np.array([float(r["censor_time"]) for r in rows if float(r["censor_time"]) >= 0])
    e_t_rec = float(np.mean(t_events)) if len(t_events) else float("nan")
    # P1-frozen paired clock: each episode contributes exactly one (event, censor)
    # value, with the other = -1. km_rmst requires the two arrays to be the SAME
    # length and pair per-episode (event time OR censor time). Passing the
    # disjoint arrays above would mis-pair and corrupt RMST.
    ev_all = np.array([float(r["recovery_event_time"]) for r in rows], dtype=float)
    ce_all = np.array([float(r["censor_time"]) for r in rows], dtype=float)
    rmst80 = km_rmst(ev_all, ce_all, TAU_PRIMARY)
    rmst220 = km_rmst(ev_all, ce_all, TAU_FULL)
    return {
        "n": n, "success": succ, "collision": coll, "P_rec": p_rec,
        "E_Trec_recovered": e_t_rec, "RMST80": rmst80, "RMST220": rmst220,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="raw episode CSV (8400 rows, raw-results-lock-v1.0)")
    parser.add_argument("--out-md", default="docs/statistics/p3a_ood_results_v1_1/p3a_ood_analysis.md")
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument("--rng-seed", type=int, default=RNG_SEED)
    args = parser.parse_args()

    rows = load_rows(Path(args.raw))
    if len(rows) != 8400:
        print(f"FATAL: expected 8400 rows, got {len(rows)}")
        return 1
    print(f"loaded {len(rows)} rows; B={args.n_boot}, rng_seed={args.rng_seed}")

    # ---- seed-wise Delta^OOD (point estimates) ----
    seed_delta: dict[str, float] = {}
    seed_cell: dict[tuple[str, str], float] = {}
    for seed in SEEDS:
        deltas = []
        for cell in CELLS_ORDER:
            f = [r for r in rows if r["method"] == FULL_NAME and r["train_seed"] == seed and r["cell"] == cell]
            m = [r for r in rows if r["method"] == MAPPO_NAME and r["train_seed"] == seed and r["cell"] == cell]
            f_ev, f_ce = block_times(f)
            m_ev, m_ce = block_times(m)
            d = km_rmst(f_ev, f_ce, TAU_PRIMARY) - km_rmst(m_ev, m_ce, TAU_PRIMARY)
            deltas.append(d)
            seed_cell[(seed, cell)] = d
        seed_delta[seed] = float(np.mean(deltas))
    mean_agg = float(np.mean(list(seed_delta.values())))
    sd_agg = float(np.std(list(seed_delta.values()), ddof=1))

    # ---- hierarchical paired bootstrap ----
    boot_mean, boot_sd, ci_lo, ci_hi, p_lt0 = hierarchical_bootstrap_delta(rows, args.n_boot, args.rng_seed)

    # ---- per-cell secondary stats (seed-averaged), all methods ----
    methods = [FULL_NAME, MAPPO_NAME, "happo", "param_matched_single"]
    per_cell_all: dict[tuple[str, str], dict] = {}
    for method in methods:
        for seed in SEEDS:
            for cell in CELLS_ORDER:
                block = [r for r in rows if r["method"] == method and r["train_seed"] == seed and r["cell"] == cell]
                per_cell_all[(method, cell)] = per_cell_all.get((method, cell), []) + [cell_stats(block)]

    # ---- family effects (Full - MAPPO, RMST80, seed-averaged) ----
    family_effect: dict[str, float] = {}
    for fam, clist in FAMILIES.items():
        eff = 0.0
        for c in clist:
            for seed in SEEDS:
                eff += seed_cell[(seed, c)]
        family_effect[fam] = eff / (len(clist) * 3)

    # ---- Gate verdict ----
    if mean_agg < 0 and all(v < 0 for v in seed_delta.values()) and ci_hi < 0 and p_lt0 >= 0.95:
        gate = ("A", "early post-failure recovery advantage persists across unseen distribution shifts.")
    elif mean_agg < 0 and all(v < 0 for v in seed_delta.values()) and not all(abs(f) < 1e-9 for f in family_effect.values()):
        # aggregate favorable, seeds consistent, but one or more families reversed
        if any(v > 0 for v in family_effect.values()):
            gate = ("B", "the advantage persists under selected distribution shifts and is family-dependent.")
        else:
            gate = ("A", "early post-failure recovery advantage persists across unseen distribution shifts.")
    elif mean_agg < 0:
        gate = ("B", "the advantage persists under selected distribution shifts and is family-dependent.")
    else:
        gate = ("C", "the early-recovery advantage is distribution-dependent.")

    # ---- write report ----
    lines = ["# P3-A OOD Statistical Analysis (P3-A.3b)", "",
             f"- raw input: `{args.raw}`", f"- rows: {len(rows)}", f"- B={args.n_boot}, RNG={args.rng_seed}", ""]
    lines.append("## Primary: Full vs MAPPO, RMST80, 7-cell equal-weight aggregate")
    lines.append("")
    lines.append("| seed | Delta^OOD_s |")
    lines.append("|---|---|")
    for seed in SEEDS:
        lines.append(f"| s{seed} | {seed_delta[seed]:+.3f} |")
    lines.append(f"| **mean** | **{mean_agg:+.3f} ± {sd_agg:.3f}** |")
    lines.append("")
    lines.append(f"hierarchical paired bootstrap (B={args.n_boot}): "
                 f"mean {boot_mean:+.3f} (SD {boot_sd:.3f}), 95% CI [{ci_lo:+.3f}, {ci_hi:+.3f}], "
                 f"P(Delta<0) = {p_lt0:.4f}")
    lines.append("")
    lines.append(f"Gate: **{gate[0]}** — {gate[1]}")
    lines.append("")

    lines.append("## Seed x cell Delta^80 (Full - MAPPO, RMST80)")
    lines.append("")
    lines.append("| seed | " + " | ".join(CELLS_ORDER) + " |")
    lines.append("|" + "|".join(["---"] * (1 + len(CELLS_ORDER))) + "|")
    for seed in SEEDS:
        lines.append(f"| s{seed} | " + " | ".join(f"{seed_cell[(seed, c)]:+.2f}" for c in CELLS_ORDER) + " |")
    lines.append("")

    lines.append("## Family effects (Full - MAPPO, RMST80, seed-averaged)")
    lines.append("")
    for fam, eff in family_effect.items():
        lines.append(f"- {fam} ({'+'.join(FAMILIES[fam])}): {eff:+.3f}")
    lines.append("")

    lines.append("## Per-cell secondary (seed-averaged, per method)")
    lines.append("")
    header = ["cell", "method", "RMST80", "RMST220", "P_rec", "E[T_rec|rec] (cond)", "collision"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for cell in CELLS_ORDER:
        for method in methods:
            sts = per_cell_all[(method, cell)]
            rm80 = np.mean([s["RMST80"] for s in sts])
            rm220 = np.mean([s["RMST220"] for s in sts])
            pr = np.mean([s["P_rec"] for s in sts])
            etr = np.nanmean([s["E_Trec_recovered"] for s in sts])
            col = np.mean([s["collision"] for s in sts])
            lines.append(f"| {cell} | {method} | {rm80:.1f} | {rm220:.1f} | {pr:.3f} | {etr:.1f} | {col:.3f} |")
    lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append("- HAPPO and Wider-SG are strong-reference comparators, not primary.")
    lines.append("- Collision is reported separately and does not enter the primary headline.")
    lines.append("- No re-tuning of tau / cells / checkpoints / family weights / recovery "
                 "definition is permitted after this first output.")
    lines.append("")

    out = Path(args.out_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    print(f"RESULT seed_delta={ {s: round(v, 3) for s, v in seed_delta.items()} } "
          f"mean={mean_agg:+.3f} sd={sd_agg:.3f} bootCI=[{ci_lo:+.3f},{ci_hi:+.3f}] "
          f"P(lt0)={p_lt0:.4f} family={ {k: round(v, 3) for k, v in family_effect.items()} } "
          f"gate={gate[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
