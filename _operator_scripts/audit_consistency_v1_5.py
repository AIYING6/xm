# audit_consistency_v1_5.py — Four-layer consistency audit of paper_latex_3d_en against the
# locked v1.5 evidence chain. Generates:
#   docs/paper_assets_v1_5/consistency_replacement_map_v1_5.csv
#   docs/paper_assets_v1_5/consistency_audit_v1_5.md
#   docs/paper_assets_v1_5/consistency_audit_summary_v1_5.md
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper_assets_v1_5"

# (file, line, issue_type, severity, original, replacement, evidence)
# issue_type in {mechanism_fact, experiment_claim, number_scope, contribution_level}
ITEMS = [
    # ---------------- main.tex ----------------
    ("main.tex", 15, "contribution_level", "P2",
     r"\title{Multi-Relation Role Graph Reinforcement Learning for Heterogeneous UAV Kill-Chain Recovery under Limited Communication and Intermittent Sensing}",
     r"\title{Task-Graph-Driven Multi-Relation Coordination for Fast Post-Failure Recovery in Multi-UAV Semantic Search}",
     "PAPER_RESTRUCTURE_MAP §1; RPG is auxiliary, task-graph is the core narrative"),
    ("main.tex", 24, "mechanism_fact", "P0",
     "constructs separate perception, communication, and dynamic task-support relations",
     "constructs separate perception, communication, and task-support relations (task-support is a static task-dependent relation mask, not a dynamic gate)",
     "TASK_SUPPORT_MECHANISM_PROTOCOL Addendum C: no post-failure activation increase; pre 0.141→early 0.092"),
    ("main.tex", 24, "mechanism_fact", "P1",
     "performs role-pair-conditioned message propagation under centralized training and decentralized execution",
     "applies state-dependent edge-feature-modulated attention over multi-relation graphs (a static role-pair modulation is retained as an auxiliary component)",
     "RPG REMOVE/simplify verdict (robustness/efficiency locks)"),
    ("main.tex", 24, "experiment_claim", "P0",
     "improves post-failure kill-chain recovery over no-graph and single-graph baselines under a five-seed fixed-budget evaluation. The full method achieves an 88.6% recovery rate, compared with 53.2% ... 21.8% ...",
     "achieves near-saturated recovery reliability (0.971±0.021) while reducing post-failure recovery latency by ~38%/34%/59% vs MAPPO/HAPPO/param-matched (3 training seeds, 10,800-episode held-out)",
     "canonical_results_v1_5 table1_held_out (locked)"),
    ("main.tex", 24, "experiment_claim", "P0",
     "Mechanism ablations show that removing role-pair-conditioned message gating significantly degrades recovery",
     "Ablations show Gate Prior is a strong contributor (recovery 0.972→0.772 without it); Task-Support contributes empirically (0.972→0.892); role-pair modulation shows no consistent independent gain (0.972→0.990 without it)",
     "canonical table2_ablation (locked)"),
    ("main.tex", 24, "experiment_claim", "P0",
     "removing task-support relations lowers mean recovery with stronger seed-level heterogeneity",
     "removing task-support relations lowers held-out recovery (0.972→0.892) and increases recovery latency (10.8→15.0)",
     "canonical table2_ablation (locked)"),
    # ---------------- 01_introduction ----------------
    ("01_introduction.tex", 9, "experiment_claim", "P0",
     "the multi-relation policy restores the kill chain more reliably than no-graph and single-graph baselines under a five-seed fixed-budget evaluation",
     "the multi-relation policy reaches near-saturated recovery reliability (0.971±0.021, 3 seeds) and restores the kill chain substantially faster than MAPPO/HAPPO/param-matched baselines",
     "canonical table1_held_out"),
    ("01_introduction.tex", 13, "contribution_level", "P2",
     r"\item We propose a multi-relation role graph policy with perception, communication, task-support relations, and role-pair-conditioned message propagation for decentralized actors.",
     r"\item We propose a task-graph-driven multi-relation graph policy (perception/communication/task-support relations with state-dependent edge-feature-modulated attention) for decentralized actors; a static role-pair modulation is retained as an auxiliary component.",
     "PAPER_RESTRUCTURE_MAP §14 (contribution 1)"),
    ("01_introduction.tex", 15, "experiment_claim", "P0",
     r"\item We provide a five-seed fixed-budget evidence chain showing improved relay-failure recovery over no-graph and single-graph baselines, supported by seed-aware bootstrap, mechanism ablations, and failure-aligned analysis.",
     r"\item We provide a locked three-seed evidence chain (10,800-episode held-out, 10,500-episode robustness, efficiency profiling) showing near-saturated recovery reliability with substantially lower post-failure recovery latency, plus Gate Prior mechanism analysis.",
     "locked evidence chain (held-out/robustness/efficiency/gate-prior locks)"),
    # ---------------- 04_method ----------------
    ("04_method.tex", 13, "contribution_level", "P1",
     "Role-pair-conditioned message propagation is used so that messages can depend on sender role, receiver role, and relation type. This is the key distinction from a single homogeneous graph encoder.",
     "State-dependent edge-feature-modulated attention over separate relation channels is used so messages depend on relation type and edge features; role-pair modulation is a static auxiliary modulation. The key distinction from a homogeneous encoder is the multi-relation task-graph structure.",
     "RPG REMOVE/simplify; edge-feature modulation is the claimed mechanism"),
    ("04_method.tex", 28, "contribution_level", "P1",
     r"\caption{Multi-relation role graph. Perception, communication, task-support, and attack-window relations have different semantics, while role-pair-conditioned messages control information flow between heterogeneous platforms.}",
     r"\caption{Multi-relation task graph. Perception, communication, and task-support relations have different semantics and are processed by state-dependent, edge-feature-modulated attention; task-support acts as a task-dependent relation mask over delivered communication.}",
     "TASK_SUPPORT protocol: task-support is a relational mask over delivered communication, not an independent channel"),
    # ---------------- 05_experiments (whole chapter is v1.4 fx60; P0) ----------------
    ("05_experiments.tex", 7, "number_scope", "P0",
     "fixed-budget checkpoint rule ... 60 safety-continuation PPO updates ... actor_critic_update_0060.pt ... five training seeds and 100 matched test episodes per seed",
     "replace with the locked protocol: 3 training seeds × 977 PPO updates, held-out base_seed 745669, 2 scenarios × 4 windows × 100 episodes/seed (10,800-episode held-out), robustness base_seed 946804 (10,500 episodes), efficiency profiling locked",
     "held-out/robustness/efficiency protocols (frozen)"),
    ("05_experiments.tex", 13, "number_scope", "P0",
     "The full multi-relation method achieves an 88.6% post-failure recovery rate, compared with 53.2% ... 21.8% ... tracking from 47.5% to 77.6% ...",
     "replace with canonical table1_held_out numbers (Full recovery 0.9706±0.0213, t_rec 10.8±0.6; vs MAPPO/HAPPO/param_matched 17.4/16.3/26.2)",
     "canonical_results_v1_5 table1_held_out"),
    ("05_experiments.tex", 17, "number_scope", "P0",
     "The seed-aware bootstrap indicates ... 35.4 percentage points ... [1.2, 73.0] ... 66.8 ... [28.6, 93.8] ... single-graph baseline has a 2.8% mean collision rate",
     "delete (old bootstrap); report locked 3-seed mean ± SD and Wilson95 lower bound from canonical table1_held_out",
     "canonical_results_v1_5"),
    ("05_experiments.tex", 23, "number_scope", "P0",
     "early-failure setting ... 88.2% ... 46.6% ... 23.2% ... 41.6 pp ... [4.4, 78.6]",
     "replace with locked robustness numbers (R00–R09 degradation, ΔRecovery/Δt_rec/worst-seed) from canonical table3_robustness",
     "canonical table3_robustness"),
    ("05_experiments.tex", 35, "experiment_claim", "P0",
     "This supports role-pair-conditioned message gating as the cleanest current mechanism contribution.",
     "Delete. Locked evidence shows role-pair modulation provides no consistent independent gain (recovery 0.990 without it); do not claim it as a mechanism contribution.",
     "robustness RPG verdict REMOVE/simplify; canonical table2_ablation"),
    ("05_experiments.tex", 37, "experiment_claim", "P0",
     "Removing task-support relations also reduces mean recovery from 88.6% to 64.8%, but its seed-aware recovery interval crosses zero. Therefore ... supportive mechanism evidence rather than as a statistically decisive result.",
     "Replace with locked numbers: removing task-support lowers recovery 0.972→0.892 and raises t_rec 10.8→15.0; internal temporal analysis (pre 0.141→early 0.092→pre-rec 0.090) shows no post-failure activation increase ⇒ empirical support only.",
     "task-support-mechanism-results-lock"),
    ("05_experiments.tex", 43, "experiment_claim", "P0",
     "Figure ... shows failure-aligned tracking, connectivity, chain-closure, and recovery-CDF curves ... aggregated over the matched fixed-budget test set",
     "Replace with locked case-trajectory figures (task_support case manifest, fixed selection rule) and R00–R09 robustness degradation curves",
     "task_support_assets; canonical table3_robustness"),
    ("05_experiments.tex", 63, "experiment_claim", "P1",
     "This additional cost is modest in absolute CPU actor-forward latency for the present 3v1 setting",
     "Replace with the honest efficiency framing: Full has higher joint-decision latency (12.05 ms), lower e2e throughput (242 env-steps/s) and highest training peak memory (71.9 MB); it trades computational cost for faster task-level recovery",
     "efficiency-results-lock-v1.5.0 (canonical table4)"),
    ("05_experiments.tex", 69, "experiment_claim", "P2",
     "three-seed no-curriculum development diagnostic ... 88.9% ... 87.8% ... 2.2 percentage points",
     "remove old numbers; keep the statement that topology curriculum is a training protocol, not a primary contribution (no v1.5 claim needed)",
     "PAPER_RESTRUCTURE_MAP §12"),
    # ---------------- 06_discussion ----------------
    ("06_discussion.tex", 3, "experiment_claim", "P0",
     "The fixed-budget five-seed evaluation strengthens this claim ... improves recovery over both no-graph and single-graph baselines while maintaining zero test collisions",
     "Replace with locked framing: near-saturated reliability (0.971±0.021) with recovery latency reduced ~38%/34%/59% vs MAPPO/HAPPO/param-matched; the advantage is reliability–recovery-speed trade-off, not uniform dominance",
     "canonical table1_held_out"),
    ("06_discussion.tex", 5, "experiment_claim", "P0",
     "The strongest mechanism evidence is the role-pair-conditioned message-gating ablation ... separates in favor of the full method ... task-support relation ablation ... crosses zero",
     "Replace with: the strongest mechanism evidence is Gate Prior (cross-seed gate corr 0.962 vs 0.562, AUC 0.545 vs 0.396, worst-seed stability); Task-Support is empirical; role-pair modulation has no consistent independent gain",
     "gate-prior-mechanism-results-lock; canonical table2_ablation"),
    ("06_discussion.tex", 9, "experiment_claim", "P0",
     "the current paper-facing package uses a fixed checkpoint at update 60 ... should not be mixed with validation-selected results",
     "Replace with: results come from a locked pre-registered protocol (fixed checkpoints update_0700/update_0100 etc., validation-selected 27-checkpoint manifest, held-out base_seed 745669 used once); see formal protocol documents",
     "held-out protocol; 27-checkpoint manifest lock"),
    # ---------------- 07_conclusion ----------------
    ("07_conclusion.tex", 3, "contribution_level", "P1",
     "The method separates perception, communication, and task-support relations and uses role-pair-conditioned message propagation under centralized training and decentralized execution.",
     "The method separates perception, communication, and task-support relations processed by state-dependent edge-feature-modulated attention under centralized training and decentralized execution; Gate Prior stabilizes role-structured optimization.",
     "PAPER_RESTRUCTURE_MAP §14"),
    ("07_conclusion.tex", 5, "experiment_claim", "P0",
     "Across five training seeds and 500 matched test episodes, the full multi-relation method achieves 88.6% recovery, compared with 53.2% ... 21.8% ... removing role-pair-conditioned message gating significantly degrades recovery",
     "Across 3 training seeds and a 10,800-episode held-out, Full reaches recovery 0.971±0.021 with t_rec 10.8±0.6; ablation shows Gate Prior (0.972→0.772) and Task-Support (0.972→0.892) matter, while role-pair modulation shows no independent gain",
     "canonical tables (locked)"),
]

SEV_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # sort: file order, then severity, then line
    order = ["main.tex", "01_introduction.tex", "03_problem.tex", "04_method.tex",
             "05_experiments.tex", "06_discussion.tex", "07_conclusion.tex"]
    items = sorted(ITEMS, key=lambda x: (order.index(x[0]), SEV_ORDER[x[3]], x[1]))

    # ---- CSV replacement map ----
    with (OUT / "consistency_replacement_map_v1_5.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "line", "issue_type", "severity", "original_text",
                    "replacement_text", "evidence_source", "status"])
        for file, line, itype, sev, orig, repl, ev in items:
            w.writerow([file, line, itype, sev, orig.replace("\n", " "),
                        repl.replace("\n", " "), ev, "open"])

    # ---- audit md ----
    lines = [
        "# Consistency Audit v1.5 — paper_latex_3d_en vs locked evidence",
        "",
        "- audited: 2026-08-07",
        "- scope: mechanism_fact / experiment_claim / number_scope / contribution_level",
        "- severity: P0=factual error vs locked evidence, P1=overclaim, P2=term imprecision, P3=style",
        "- rule: P0/P1 must be zeroed before any body rewrite; P2/P3 handled during section rewrites.",
        "- numbers authority: `canonical_results_v1_5.csv` (built from locked assets only).",
        "",
        "## Critical structural finding",
        "",
        "`05_experiments.tex` (and the abstract/conclusion/discussion) still describe the OLD ",
        "v1.4 fixed-budget fx60 package (5 seeds, update-60 checkpoints, 88.6%/53.2%/21.8%, ",
        "500 matched episodes, dropout030_relay_failure). These numbers conflict with the locked ",
        "v1.5 chain and are P0. The experiments chapter must be rebuilt around RQ1–RQ6 with ",
        "canonical tables (table1_held_out / table2_ablation / table3_robustness / ",
        "table4_efficiency) and the Pareto figures.",
        "",
    ]
    cur_file = None
    for file, line, itype, sev, orig, repl, ev in items:
        if file != cur_file:
            lines.append(f"## {file}")
            cur_file = file
        lines.append(f"- **[L{line}] [{sev}] {itype}**")
        lines.append(f"  - ORIG: `{orig[:160]}{'…' if len(orig) > 160 else ''}`")
        lines.append(f"  - REPL: `{repl[:160]}{'…' if len(repl) > 160 else ''}`")
        lines.append(f"  - EVIDENCE: {ev}")
    (OUT / "consistency_audit_v1_5.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- summary md ----
    cnt = Counter(sev for _, _, _, sev, _, _, _ in items)
    by_file = defaultdict(Counter)
    for file, _, _, sev, _, _, _ in items:
        by_file[file][sev] += 1
    summ = [
        "# Consistency Audit Summary v1.5",
        "",
        f"Total items: {len(items)}",
        f"P0 (factual): {cnt['P0']}   P1 (overclaim): {cnt['P1']}   "
        f"P2 (term): {cnt['P2']}   P3 (style): {cnt['P3']}",
        "",
        "## By file",
        "| file | P0 | P1 | P2 | total |",
        "|---|---|---|---|---|",
    ]
    for f in order:
        c = by_file[f]
        summ.append(f"| {f} | {c['P0']} | {c['P1']} | {c['P2']} | {sum(c.values())} |")
    summ += [
        "",
        "## P0/P1 zero-out gate",
        "",
        "- [ ] all P0/P1 items applied via `consistency_replacement_map_v1_5.csv` (status → fixed)",
        "- [ ] `05_experiments.tex` rebuilt around RQ1–RQ6 with canonical tables/figures",
        "- [ ] title/abstract rewritten only AFTER P0/P1 cleared (no old Role-Graph/dynamic-gate narrative)",
        "- [ ] number audit: every numeric claim resolvable to a canonical row",
    ]
    (OUT / "consistency_audit_summary_v1_5.md").write_text("\n".join(summ), encoding="utf-8")

    print(f"items: {len(items)}  P0={cnt['P0']} P1={cnt['P1']} P2={cnt['P2']}")
    print(f"written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
