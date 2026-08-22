from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from statistics import mean, median, stdev


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "paper_q2_p1"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def metric_table(path: str) -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    for line in read(path).splitlines():
        if not line.startswith("| `"):
            continue
        parts = [p.strip().strip("`") for p in line.strip().strip("|").split("|")]
        if len(parts) >= 3:
            try:
                out[parts[0]] = (float(parts[1]), float(parts[2]))
            except ValueError:
                pass
    return out


def t1_pooled() -> dict[str, float]:
    for line in read("docs/T1_TELEMETRY_NATIVE_REFERENCE_REPORT.md").splitlines():
        if line.startswith("| Pooled seed mean"):
            p = [x.strip() for x in line.strip().strip("|").split("|")]
            return {"J_nominal": float(p[1]), "J_F0": float(p[2]), "J_OOD_mean": float(p[3]), "J_OOD_worst": float(p[4]), "collision": float(p[5]), "timeout": float(p[6])}
    raise RuntimeError("T1 pooled row not found")


def heldout_rows() -> list[dict[str, float | str | int]]:
    rows = []
    for line in read("docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md").splitlines():
        if not line.startswith("| UTR-SG |") and not line.startswith("| DRTP-SG |"):
            continue
        p = [x.strip() for x in line.strip().strip("|").split("|")]
        rows.append({"method": p[0], "seed": int(p[1]), "J_nominal": float(p[2]), "J_F0": float(p[3]), "J_OOD_mean": float(p[4]), "J_OOD_worst": float(p[5]), "exposure": float(p[6]), "collision": float(p[7]), "timeout": float(p[8]), "constraint": 0.0})
    if len(rows) != 6:
        raise RuntimeError(f"heldout rows found: {len(rows)}")
    return rows


def quantile(xs: list[float], q: float) -> float:
    ys = sorted(xs)
    if len(ys) == 1:
        return ys[0]
    pos = (len(ys) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return ys[lo] + (ys[hi] - ys[lo]) * (pos - lo)


def mad(xs: list[float]) -> float:
    m = median(xs)
    return median([abs(x - m) for x in xs])


def bootstrap_ci(xs: list[float], n: int = 20000) -> list[float]:
    import random
    rng = random.Random(20260822)
    vals = []
    for _ in range(n):
        sample = [xs[rng.randrange(len(xs))] for _ in xs]
        vals.append(mean(sample))
    return [quantile(vals, 0.025), quantile(vals, 0.975)]


def summarize(xs: list[float], baseline: float | None = None) -> dict[str, float | int | list[float] | None]:
    m = mean(xs)
    sd = stdev(xs) if len(xs) > 1 else 0.0
    return {"n": len(xs), "mean": m, "median": median(xs), "std": sd, "IQR": quantile(xs, .75) - quantile(xs, .25), "MAD": mad(xs), "win_count": sum(x > 0 for x in xs) if baseline is None else None, "worst_delta": min(xs), "paired_dz": m / sd if sd else None, "descriptive_seed_bootstrap_95_ci": bootstrap_ci(xs)}


def main() -> None:
    dev = metric_table("docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md")
    t1 = t1_pooled()
    hrows = heldout_rows()
    h = {}
    for method in ("UTR-SG", "DRTP-SG"):
        subset = [r for r in hrows if r["method"] == method]
        h[method] = {k: mean(float(r[k]) for r in subset) for k in ("J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "collision", "timeout", "constraint", "exposure")}
    rows = [
        {"contract": "T1_1M", "method": "UTR-SG-reference", "seed_scope": "2201-2205 pooled seed mean", **t1, "constraint": "NA", "exposure": 0.9927, "source_artifact": "docs/T1_TELEMETRY_NATIVE_REFERENCE_REPORT.md"},
        {"contract": "DRTP_development_3M", "method": "UTR-SG", "seed_scope": "1901-1902 pooled", "J_nominal": dev["J_nominal"][0], "J_F0": dev["J_F0"][0], "J_OOD_mean": dev["J_OOD_mean"][0], "J_OOD_worst": dev["J_OOD_worst"][0], "collision": 0.0136, "timeout": 0.8086, "constraint": 0.0, "exposure": 1.0, "source_artifact": "docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md"},
        {"contract": "DRTP_development_3M", "method": "DRTP-SG", "seed_scope": "1901-1902 pooled", "J_nominal": dev["J_nominal"][1], "J_F0": dev["J_F0"][1], "J_OOD_mean": dev["J_OOD_mean"][1], "J_OOD_worst": dev["J_OOD_worst"][1], "collision": 0.0014, "timeout": 0.5600, "constraint": 0.0, "exposure": 1.0, "source_artifact": "docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md"},
        {"contract": "DRTP_heldout_10M", "method": "UTR-SG", "seed_scope": "2001-2003 pooled", **h["UTR-SG"], "source_artifact": "docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md"},
        {"contract": "DRTP_heldout_10M", "method": "DRTP-SG", "seed_scope": "2001-2003 pooled", **h["DRTP-SG"], "source_artifact": "docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md"},
    ]
    fields = ["contract", "method", "seed_scope", "J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "timeout", "collision", "constraint", "exposure", "source_artifact"]
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "main_table.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    raw = [
        {"seed": 1901, "contract": "development_3M", "delta_nominal": 40.794, "delta_F0": 133.589, "delta_OOD_mean": 131.498, "delta_OOD_worst": 130.631, "delta_timeout": "NA", "direction_note": "positive on all published return deltas"},
        {"seed": 1902, "contract": "development_3M", "delta_nominal": 6.908, "delta_F0": -21.687, "delta_OOD_mean": -5.785, "delta_OOD_worst": 7.552, "delta_timeout": "NA", "direction_note": "F0/OOD mean negative; compound timeout breach +0.19"},
        {"seed": 2001, "contract": "heldout_10M", "delta_nominal": 149.059, "delta_F0": 104.265, "delta_OOD_mean": 107.200, "delta_OOD_worst": 92.626, "delta_timeout": -0.4563, "direction_note": "positive returns; timeout lower"},
        {"seed": 2002, "contract": "heldout_10M", "delta_nominal": -16.254, "delta_F0": -113.951, "delta_OOD_mean": -88.126, "delta_OOD_worst": -97.100, "delta_timeout": 0.3919, "direction_note": "severe reversal; timeout higher"},
        {"seed": 2003, "contract": "heldout_10M", "delta_nominal": 50.650, "delta_F0": 29.804, "delta_OOD_mean": 26.305, "delta_OOD_worst": 23.688, "delta_timeout": -0.0909, "direction_note": "positive returns; timeout lower"},
    ]
    with (OUT / "seed_level_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(raw[0])); w.writeheader(); w.writerows(raw)

    primary = {k: [float(r[k]) for r in raw] for k in ("delta_nominal", "delta_F0", "delta_OOD_mean", "delta_OOD_worst")}
    stratified = {}
    for contract in ("development_3M", "heldout_10M"):
        sr = [r for r in raw if r["contract"] == contract]
        stratified[contract] = {k: summarize([float(r[k]) for r in sr]) for k in ("delta_nominal", "delta_F0", "delta_OOD_mean", "delta_OOD_worst")}
    summary = {"schema": "paper-q2-p1-statistical-summary-v1", "independent_unit": "training_seed", "mixed_contract_summary_is_descriptive_only": True, "primary_metrics": {k: summarize(v) for k, v in primary.items()}, "contract_stratified": stratified, "timeout_note": "Only held-out pooled seed deltas are available in the frozen P0 audit; development timeout is retained as pooled and condition-level evidence, not imputed per seed.", "effect_size": "paired Cohen dz reported descriptively; n=5 and mixed contracts do not support broad population inference."}
    (OUT / "statistical_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    provenance = {
        "schema": "paper-q2-p1-result-provenance-v1",
        "training_started": False,
        "rows": [
            {"paper_number": "Table 2", "artifact": "artifacts/paper_q2_p1/main_table.csv", "source_artifact": "docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md; docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md; docs/T1_TELEMETRY_NATIVE_REFERENCE_REPORT.md", "aggregation": "source report pooled seed means; no episode-level independence"},
            {"paper_number": "Table 3 / Figure 6", "artifact": "artifacts/paper_q2_p1/seed_level_results.csv", "source_artifact": "docs/DRTP_Q2_PUBLICATION_VIABILITY_AUDIT.md", "contract": "development_3M and heldout_10M kept as separate strata", "aggregation": "paired DRTP-UTR deltas by training seed"},
            {"paper_number": "Figure 1/2", "artifact": "docs/PHASE_S1B_TOPOLOGY_RECONFIGURATION_VALIDATION_REPORT.md", "source_artifact": "S1B/S2 frozen mechanism reports", "aggregation": "telemetry/path audit"},
            {"paper_number": "Figure 7", "artifact": "docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md", "source_artifact": "held-out v2 final evaluation", "aggregation": "all planned rows, safety/exposure retained"},
            {"paper_number": "Supplementary limitation", "artifact": "docs/G0_FINAL_DECISION.md", "source_artifact": "G0 development-only zero-shot suite", "aggregation": "decision C; descriptive limitation only"},
        ],
        "forbidden_sources": ["paper_latex_3d_en/main.tex", "results/gate1_safety_fx60_paper_tables/*"],
        "provenance_warning": "Development 3M and held-out 10M are not one homogeneous replicate set; do not pool for confirmatory inference.",
    }
    (OUT / "result_provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    write("docs/PAPER_Q2_P1_COMPARATOR_DECISION.md", """# PAPER-Q2-P1 Comparator Decision

**Decision: `E2 — NO_FAIR_EXTERNAL_COMPARATOR`**  
**Training:** none authorized or started.

## Audit question

The current internal ladder is: standard MAPPO/graph references where contract-valid, matched Single-Graph UTR, and DRTP adaptive topology-perturbation weighting. The central controlled comparison is UTR versus DRTP because both use the same seven groups, 50% nominal anchor, SG architecture, PPO, environment, reward, actor boundary, budget, and evaluation contract; only the group-weight controller differs.

## Why no external drop-in is fair

- TAPE is topology-aware cooperative policy-gradient work, but its topology/action/task semantics do not implement the frozen heterogeneous Scout–Relay–Attacker relay-failure event.
- Robust MARL/M3DDPG addresses opponent-policy or adversarial variation with a different learner and continuous-control contract, not a drop-in CTDE comparator for this task.
- Distributionally robust Q-learning/DRRL papers are not multi-agent CTDE policy comparators and do not provide a directly reproducible actor under the frozen information boundary.
- Recent UAV relay MARL papers optimize communication, power, covert transmission, or connectivity restoration objectives rather than this mission-level relay-node topology perturbation estimand.

Forcing any of these into the environment would change the scientific problem or the fairness contract. The correct response is to strengthen related work and disclose that the comparison is an internal, capacity- and topology-group-matched ladder.

## Final manuscript handling

Do not add a comparator zoo. State explicitly that external methods were reviewed but no fair drop-in was identified. If a reviewer later requires one, create a separately frozen training request; P1 does not authorize it.
""")
    write("docs/PAPER_Q2_P1_ABLATION_DECISION.md", """# PAPER-Q2-P1 Ablation Decision

**Decision: `A0 — EXISTING_UTR_VS_DRTP_SUFFICIENT`**  
**Training:** none authorized or started.

UTR and DRTP already isolate the primary method question: whether adaptive topology-group weighting adds value beyond uniform exposure. The contract confirms identical:

- SG architecture and 116,728 parameters;
- PPO, critic, reward, environment, failure semantics and actor boundary;
- seven topology groups and 50% nominal anchor;
- training budget, seed policy, final checkpoint and evaluation aggregation.

The only intended difference is fixed uniform `q_k=1/6` versus bounded adaptive `q`. This is the mandatory causal ablation and is already represented by the historical paired evidence. It must appear in the main paper, not only in supplementary material. The full seed-level record, including weak and reversed seeds, must be retained; the paper must not claim universal benefit or seed-stable superiority.

Fixed non-uniform weighting and nominal-anchor removal are not required to answer the primary reviewer question and would reopen algorithm development. No ablation zoo is justified.
""")
    write("docs/PAPER_Q2_P1_SCALABILITY_DECISION.md", """# PAPER-Q2-P1 Scalability Decision

**Decision: `S0 — EXISTING_ARCHITECTURE_NOT_FAIRLY_SCALABLE`**  
**Training/evaluation:** none started.

The environment loops over `num_blue`, but the frozen S2 configuration is explicitly a three-blue-role system and requires `num_blue` to match the `blue_types` list. The shared observation dimension depends on `num_blue`; the role semantics, Relay-failure contract, legal support paths, and task geometry would need a new configuration and a new failure/provenance contract. The critic input dimension also changes with `num_blue`, so the existing 3-UAV checkpoint is not a valid zero-shot 4/5-UAV checkpoint.

Therefore a 4/5-UAV study would require retraining and a separately frozen environment/evaluation contract. It is scientifically meaningful future work, but not a minimal zero-training closure item. The paper scope is explicitly the heterogeneous 3-UAV setting, with scalability stated as a limitation rather than manufactured through an unfair table.
""")
    write("docs/PAPER_Q2_P1_STATISTICAL_RESULTS.md", """# PAPER-Q2-P1 Statistical Results

The machine-readable sources are `artifacts/paper_q2_p1/main_table.csv`, `seed_level_results.csv`, and `statistical_summary.json`. The independent unit is the training seed. Development 3M and held-out 10M are separate contract strata.

## Historical paired DRTP − UTR summary

| Metric | Wins | Mean | Median | SD | IQR | MAD | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nominal | 4/5 | +46.231 | +40.794 | 63.390 | 43.742 | 33.886 | −16.254 |
| F0 | 3/5 | +26.404 | +29.804 | 99.467 | 125.952 | 51.491 | −113.951 |
| OOD mean | 3/5 | +34.218 | +26.305 | 88.629 | 112.985 | 80.895 | −88.126 |
| OOD worst | 4/5 | +31.479 | +23.688 | 87.658 | 85.074 | 16.136 | −97.100 |

The exact machine-readable summary is authoritative. These dispersion values are deterministic seed-level descriptive statistics over the five historical paired deltas; they are not population estimates.

## Absolute pooled results

Development 3M: UTR `147.157/127.929/120.607/103.149`; DRTP `171.007/183.880/183.464/172.241`, in the order nominal/F0/OOD mean/OOD worst. Failure collision was `0.0136` versus `0.0014`, timeout `0.8086` versus `0.5600`, and constraint violation was zero for both.

Held-out 10M: UTR `160.341/162.187/155.021/138.354`; DRTP `221.493/168.893/170.147/144.758`. Held-out DRTP timeout was mixed and collision was higher in all three seeds; the held-out contract therefore remains FAIL.

## Interpretation

The mean/median gains are publication-relevant descriptive effects, not evidence of seed-stable superiority. Seed1902 and held-out seed2002 remain in the main reliability narrative. The UTR-versus-DRTP comparison is the mandatory causal ablation and must remain in the main paper.
""")
    write("docs/PAPER_Q2_RESULT_PROVENANCE.md", """# PAPER-Q2 Result Provenance

The machine-readable version is `artifacts/paper_q2_p1/result_provenance.json`.

| Paper object | Source | Contract | Aggregation |
|---|---|---|---|
| Table 2 | T1 reference, DRTP development, DRTP held-out reports | T1 1M; DRTP 3M; DRTP held-out 10M | pooled seed means within each contract only |
| Table 3 / Fig. 6 | `DRTP_Q2_PUBLICATION_VIABILITY_AUDIT.md` | paired historical seed audit | DRTP−UTR by training seed |
| Fig. 1/2 | S1B/S2 mechanism reports | S2 frozen | topology/path telemetry |
| Fig. 7 | held-out v2 audit | 2001–2003, 10M | all safety/exposure rows retained |
| Supplement | FL/G0/negative-method reports | separate diagnostic contracts | limitation/negative evidence |

## Non-comparable sources

`paper_latex_3d_en/main.tex` and `results/gate1_safety_fx60_paper_tables/` belong to the legacy recovery/fx60 evidence chain. They must not supply a DRTP table, figure, or claim.

## Contract rule

Every manuscript number must retain method, training seed, budget, tape/condition, checkpoint rule, evaluator/aggregation source, and commit/hash where available. Development and held-out evidence are never silently pooled as one confirmatory sample.
""")
    write("docs/PAPER_Q2_P1_FINAL_DECISION.md", """# PAPER-Q2-P1 Final Decision

**Final: `A — MANUSCRIPT_READY_WITH_EXISTING_ASSETS`**

No new training is required for the minimal publication gap closure. The current assets support a complete, bounded manuscript if the paper:

1. uses the frozen relay-failure → legal topology/path reconfiguration → mission degradation mainline;
2. presents UTR versus DRTP as the core matched comparison;
3. reports all historical seeds, including seed1902 and held-out seed2002;
4. treats development NO-GO and held-out FAIL as immutable limitations;
5. scopes the result to the 3-UAV heterogeneous setting;
6. does not claim stable, guaranteed, universal, or consistently superior robustness.

External comparator: no fair drop-in identified (E2).  
Ablation: existing UTR vs DRTP is sufficient and mandatory in the main paper (A0).  
Scalability: not fairly zero-shot scalable under the frozen contract (S0).  
New training: none required or authorized by P1.
""")

    write("paper/q2_draft/abstract.md", """# Abstract

## Version A — Conservative Q2

Relay-node failures in heterogeneous multi-UAV missions can reorganize legal communication and task-support paths without creating a complete information blackout. We formulate this event as a topology-robust coordination problem and study Distributionally Robust Topology-Perturbation SG-MAPPO (DRTP-SG-MAPPO), which retains a matched single-graph MAPPO architecture while adaptively reweighting predefined topology-perturbation groups around a fixed nominal exposure anchor. Against the topology-group-matched Uniform Topology Randomization SG-MAPPO baseline, DRTP shows substantial average and median gains in the historical paired audit across nominal, canonical failure, and out-of-distribution timing, duration, and compound conditions. The same evidence also reveals non-negligible sensitivity to training initialization, including an adverse held-out seed. We therefore present DRTP as a high-upside, seed-sensitive method rather than a uniformly reliable robustness solution. The study reports absolute mission performance, paired seed-level effects, safety, exposure validity, and topology/path telemetry under frozen contracts.

## Version B — Stronger but bounded

Communication topology disruptions are a distinct source of non-stationarity in heterogeneous UAV coordination: a failed relay can change the composition of legal paths and task support even when direct communication remains available. We introduce DRTP-SG-MAPPO, an architecture-preserving training strategy that anchors nominal exposure and adaptively emphasizes difficult topology-perturbation groups using bounded group weights. Across the frozen historical evaluation assets, DRTP delivers a strong average and median robustness upside relative to uniform topology randomization, including timing, duration, and compound out-of-distribution conditions. This upside is not seed-stable: one development seed and one held-out seed show materially adverse outcomes, and safety gains are not uniform. The resulting contribution is an evidence-bounded study of adaptive topology-perturbation training and of why seed-level reliability must accompany pooled robustness metrics in heterogeneous UAV MARL.
""")
    write("paper/q2_draft/title_shortlist.md", """# Title Shortlist

1. **Topology-Robust Heterogeneous Multi-UAV Coordination under Relay-Node-Induced Communication-Path Reconfiguration**
2. **Distributionally Robust Topology-Perturbation Learning for Heterogeneous UAV Cooperation under Relay Failures**
3. **When Relay Failure Rewrites the Path: Seed-Sensitive Topology-Robust MARL for Heterogeneous UAV Teams**
4. **Adaptive Topology-Perturbation Training for Relay-Failure Robust Heterogeneous UAV Coordination**
5. **Average Robustness versus Seed Reliability in Heterogeneous UAV Coordination under Communication Topology Disruptions**

The shortlist intentionally excludes “stable”, “guaranteed”, “consistent”, “recovery”, and “information restoration”.
""")
    write("paper/q2_draft/01_introduction.md", """# 1. Introduction

Heterogeneous UAV teams depend on communication and task-support relationships that are shaped by role, geometry, sensing, and link legality. A Scout may provide target information, a Relay may support a multi-hop path, and an Attacker may convert the available support into mission progress. The resulting coordination problem is not defined only by each vehicle's local dynamics; it is also defined by the directed communication–task graph through which useful support can be composed.

Relay failure is therefore a structural perturbation of coordination. In the frozen task, the failed Relay does not imply a complete information blackout: a physically legal Scout-to-Attacker direct path may remain available. The event instead changes path composition and task-support relations, and the mission score can degrade as the team reorganizes. This distinction matters because a method that improves robustness must be evaluated against topology/path reconfiguration, not against an unsupported claim of lost-information recovery.

Existing robust MARL studies address several forms of uncertainty, adversarial variation, or topology-aware coordination, but their contracts do not directly resolve the present combination of heterogeneous roles, directed legal links, relay-node failure, and out-of-distribution timing/duration perturbations. A second challenge is training exposure: uniform sampling treats predefined topology groups equally even when their learned difficulty differs. The question is whether adaptive emphasis can improve the average robustness profile without changing the actor architecture or information boundary.

We study this question with Distributionally Robust Topology-Perturbation SG-MAPPO (DRTP-SG-MAPPO). DRTP retains the 116,728-parameter matched Single-Graph MAPPO backbone, the PPO objective, reward, environment, and decentralized actor information. It changes only the training distribution: nominal episodes retain a 50% anchor, while six failure/topology groups receive bounded adaptive weights. Uniform Topology Randomization SG-MAPPO (UTR-SG-MAPPO) uses the same groups and anchor with uniform group weights.

The evidence supports three bounded conclusions. First, relay failure produces legal topology/path reorganization and mission degradation. Second, DRTP has a substantial average and median robustness upside in the historical paired audit. Third, this upside coexists with non-negligible initialization sensitivity, including the development seed1902 limitation and held-out seed2002 reversal. We therefore treat seed-level reliability, safety, and exposure validity as first-class outcomes rather than presenting pooled reward as a sufficient robustness claim.

Our contributions are: (i) a frozen heterogeneous communication–task graph robustness formulation for relay failures; (ii) an architecture-preserving adaptive topology-perturbation training strategy; (iii) paired nominal/F0/OOD and safety evaluation with explicit risk-set exposure validity; and (iv) a transparent analysis of average robustness gains and their seed-sensitive boundary.
""")
    write("paper/q2_draft/02_related_work.md", """# 2. Related Work

## Robust multi-agent reinforcement learning

Robust MARL has considered continuous-action coordination under changes in other agents' policies and adversarial variation. Such work motivates robustness as a multi-agent learning objective, but the perturbation studied here is a relay-node-induced change in a legal communication–task graph. The distinction is important: the present task does not replace the mission with an adversarial game or assume that robustness can be summarized by a worst-case opponent.

## Topology-aware and communication-aware MARL

Topology-aware policy-gradient methods explicitly model agent relationships, while communication-aware UAV methods often optimize connectivity, relay selection, power, or information exchange. These studies establish the relevance of graph structure to coordination. Our focus is narrower and more operational: a fixed heterogeneous UAV mission undergoes a physically defined Relay failure, and the evaluation follows the resulting path and task-support reorganization across canonical and OOD conditions.

## Distributionally robust and adaptive environment weighting

Distributionally robust RL formalizes performance under distributional or model shifts, including worst-case distributional optimization and robust Markov decision processes. DRTP is deliberately more modest. It is an empirical bounded weighting strategy over seven predeclared topology-perturbation groups, with unchanged PPO and no claim of a general DRMDP guarantee. The paper's contribution is therefore the combination of topology-specific problem semantics, adaptive exposure, and reliability-aware evaluation rather than a new general robust-RL theorem.

Representative primary sources include [Robust Multi-Agent Reinforcement Learning](https://aima.eecs.berkeley.edu/~russell/papers/aaai19-marl.pdf), [TAPE](https://ojs.aaai.org/index.php/AAAI/article/view/29699), [Distributionally Robust Q-Learning](https://proceedings.mlr.press/v162/liu22a.html), [On the Foundation of Distributionally Robust Reinforcement Learning](https://arxiv.org/abs/2311.09018), [Fast connectivity restoration of UAV communication networks](https://doi.org/10.1016/j.adhoc.2025.103785), and [Multi-hop UAV relay covert communication](https://doi.org/10.1016/j.cja.2025.103440). Their different environments and objectives are why none is used as a drop-in external comparator in the current contract.
""")
    write("paper/q2_draft/03_problem_formulation.md", """# 3. Problem Formulation

We consider a heterogeneous team with Scout, Relay, and Attacker roles and a target. The directed adjacency convention is `A[receiver, sender]`: entry `A[i,j]` indicates that receiver `i` can use a legal relation from sender `j`. Perception, communication, and task-support relations are generated from the frozen S2 environment and remain subject to local legality.

Let `G_t` denote the communication–task graph and `J` the mission score. A nominal episode has no Relay failure. In a failure episode, the prescribed Relay node is unavailable during the frozen onset/duration condition. The key event is:

`G_t^comm -> G_{t+}^comm`,

followed by a change in path composition, support-source availability, and coordination geometry. The analysis does not assume that all target information disappears. In particular, a legal direct Scout-to-Attacker path may remain available after Relay failure.

The primary paired endpoint is the nominal–failure degradation `Delta_J = J_nominal - J_failure`, accompanied by absolute `J_nominal`, `J_F0`, `J_OOD_mean`, `J_OOD_worst`, timeout, collision, constraint violation, exposure, and topology/path telemetry. OOD conditions vary failure timing, duration, and their compound combinations. Overall performance retains every scheduled episode, including episodes that terminate before failure onset. Trigger validity is assessed separately among episodes alive immediately before scheduled onset.

The policy is decentralized at execution. Actors receive only the frozen legal local observation, node/edge features, roles, and adjacency. Training-sampler labels, failure labels, global routes, future links, and hidden simulator truth are not actor inputs.
""")
    write("paper/q2_draft/04_method.md", """# 4. Method

## 4.1 Matched Single-Graph backbone

DRTP-SG-MAPPO keeps the existing 116,728-parameter Single-Graph actor/critic and standard PPO settings. It adds no encoder, relation branch, recurrent module, reward term, critic input, or inference-time module. UTR-SG-MAPPO is the capacity- and topology-group-matched comparator.

## 4.2 Topology-perturbation groups

Training episodes are assigned to nominal `N`, canonical failure `F0`, early timing `TE`, late timing `TL`, short duration `DS`, long duration `DL`, or compound `CP`. The nominal exposure is fixed at `p_N=0.50`. For UTR, the remaining six groups have `q_k=1/6`. Each group's scenario members are sampled uniformly.

## 4.3 Bounded adaptive weighting

The conceptual robust objective is

`max_theta [ p_N J_N(theta) + (1-p_N) min_{q in Q} sum_k q_k J_k(theta) ]`,

where `Q={q in Delta^6: 0.05 <= q_k <= 0.35}`. The implementation approximates the inner distribution only through episode-sampling weights. Group returns are accumulated between adaptation boundaries, and the nominal return is the competence anchor. Difficulty is the clipped normalized nominal-minus-group return gap. The candidate update is exponentiated-gradient weighting followed by smoothed projection onto `Q`; the frozen constants are warm-up 128 updates, adaptation interval 32, EMA coefficient 0.20, temperature 1.00, smoothing 0.50, `d_max=2.00`, and `epsilon=1e-8`.

## 4.4 Information and inference boundary

Group labels, selected failure timing/duration, EMA values, difficulty, and `q` exist only in the sampler/logger. They are absent from actor and critic observations and from evaluation. Thus DRTP changes training exposure, not the policy's legal information set.
""")
    write("paper/q2_draft/05_experimental_setup.md", """# 5. Experimental Setup

## 5.1 Contracts and strata

The clean T1 UTR reference uses five 1M seeds (2201–2205). DRTP development uses seeds 1901 and 1902 at the frozen 3M endpoint. Held-out confirmation uses seeds 2001–2003 at the frozen 10M endpoint. These strata are reported separately because their budgets, tapes, and purposes differ. No canonical seeds are used in this paper-convergence stage.

## 5.2 Baselines and fairness

UTR and DRTP share the SG backbone, PPO, reward, S2 environment, seven groups, nominal anchor, seed policy, final-checkpoint rule, and evaluation aggregation. Their only intended method difference is fixed versus adaptive group weighting. Legacy EA-RG recovery and Gate1 tables are excluded because their estimands and contracts differ.

## 5.3 Mandatory main-paper ablation

The primary ablation is `UTR-SG-MAPPO vs DRTP-SG-MAPPO`. It is a causal design comparison, not a supplementary-only baseline: the two methods have identical SG architecture and parameter count (116,728), PPO and critic, seven topology-condition groups, 50% nominal anchor, training budget, and evaluation protocol. The only intended difference is uniform perturbation weighting versus adaptive DRTP weighting. Every seed is retained, including weak or reversed outcomes, and the interpretation uses paired effect sizes, win counts, medians, and worst degradation; no universal-benefit or seed-stability claim is permitted.

## 5.4 Metrics

Primary metrics are `J_F0`, `J_OOD_mean`, `J_OOD_worst`, and timeout. Secondary metrics are nominal score, collision, constraint violation, exposure, survival to onset, risk-set trigger validity, path switching, task-support availability, and maneuver/control burden. Training seed is the independent statistical unit. All planned episodes remain in unconditional return and safety summaries.

## 5.5 Statistical reporting

Every seed is shown. We report paired DRTP−UTR differences, win count, mean, median, standard deviation, IQR/MAD, worst degradation, and descriptive seed-level intervals where defensible. Five seeds are not treated as a basis for universal or seed-stable claims.
""")
    write("paper/q2_draft/06_results.md", """# 6. Results

## 6.1 Relay failure changes topology and mission support

The S1/S2 audits show that Relay failure changes legal path composition and task-support structure while legal direct alternatives can remain. The resulting mission degradation is therefore interpreted as a coordination/topology effect, not as evidence of complete information loss.

## 6.2 Main robustness performance

At the 3M development endpoint, pooled UTR versus DRTP values are respectively `147.157` versus `171.007` for nominal score, `127.929` versus `183.880` for F0, `120.607` versus `183.464` for OOD mean, and `103.149` versus `172.241` for OOD worst. Failure collision is `0.0136` versus `0.0014`, timeout is `0.8086` versus `0.5600`, and both constraint rates are zero. These pooled values are positive descriptive evidence, but the development contract remains NO-GO because seed/condition retention rules failed.

## 6.3 Seed-level effects

Across the five historical paired records, DRTP−UTR mean/median gains are +26.404/+29.804 for F0, +34.218/+26.305 for OOD mean, and +31.479/+23.688 for OOD worst. The nominal mean/median gain is +46.231/+40.794. These numbers coexist with seed1902 negative F0/OOD-mean deltas and held-out seed2002 severe reversal; all five records must be plotted.

## 6.4 Held-out reliability and safety

Held-out pooled DRTP versus UTR values are `221.493/168.893/170.147/144.758` versus `160.341/162.187/155.021/138.354` for nominal/F0/OOD mean/OOD worst. The held-out contract still FAILS: seed2002 has DRTP F0 `72.970` versus UTR `186.921`, OOD worst `53.597` versus `150.697`, and timeout `0.9064` versus `0.5145`. Collision is higher for DRTP in all three held-out seeds. The pooled upside cannot erase these reliability and safety outcomes.

## 6.5 Mandatory UTR-versus-DRTP ablation

The main-paper ablation is the matched comparison below. Because architecture, capacity, PPO, topology groups, nominal anchor, budget, and evaluation contract are held fixed, the intended causal contrast is uniform perturbation weighting (`UTR`) versus adaptive DRTP weighting (`DRTP`).

| Metric | UTR-SG | DRTP-SG | Pooled difference | Historical paired win count | Paired effect size (descriptive dz) |
|---|---:|---:|---:|---:|---:|
| Nominal | 147.157 | 171.007 | +23.850 | 4/5 | +0.729 |
| F0 | 127.929 | 183.880 | +55.951 | 3/5 | +0.265 |
| OOD mean | 120.607 | 183.464 | +62.857 | 3/5 | +0.386 |
| OOD worst | 103.149 | 172.241 | +69.092 | 4/5 | +0.359 |
| Timeout | 0.8086 | 0.5600 | -0.2486 | contract-stratified | descriptive; not pooled across contracts |

The table is descriptive evidence for the adaptive-weighting ablation, not a claim of universal benefit. The full five-seed paired record remains part of the main-paper evidence: seed1902 is negative for F0 and OOD mean, and held-out seed2002 is a severe reversal. Accordingly, the manuscript reports mean, median, win count, worst degradation, and seed dispersion, and explicitly avoids “consistently outperforms” or “seed-stable” language.

## 6.6 OOD and mechanism presentation

The final figures should separate early/late timing, short/long duration, and compound conditions, then identify the worst condition per seed. Mechanism panels should show path switching, task-support source, and mission-score change rather than imply information restoration.
""")
    write("paper/q2_draft/07_discussion.md", """# 7. Discussion

The evidence supports a narrow but useful conclusion: adaptive weighting over predefined topology perturbations can produce a strong average and median robustness upside while preserving the same policy architecture and legal information boundary. This is an empirical training-distribution result, not a general robustness guarantee.

The most important limitation is seed sensitivity. Development seed1902 violates the frozen retention contract in F0/OOD mean and shows a condition-level timeout breach. Held-out seed2002 is a severe reversal at 10M, with lower F0/OOD outcomes and higher timeout. No single actionable adaptive-training failure mechanism was identified by the forensic review, so these outcomes must be treated as genuine reliability evidence rather than as removable anomalies.

Safety is mixed. Development pooled collision and timeout are favorable for DRTP, but held-out collision is higher for DRTP in all three seeds and timeout reverses sharply at seed2002. The manuscript therefore does not claim that DRTP improves safety. Constraint violations remain zero in the cited audits.

The current evidence is limited to a heterogeneous three-UAV setting. The frozen architecture can be parameterized by agent count in code, but a fair 4/5-UAV study would require new role configurations, critic dimensions, failure semantics, and retraining. The paper should state this scope boundary rather than present an unsupported zero-shot scalability claim. Similarly, G0 found no actionable additional structural-topology generalization gap on its development-only suite; that result is a limitation/context statement, not a universal generalization claim.

Finally, DRTP is related to distributionally robust and topology-aware learning, but its defensible novelty lies in the integrated problem/evaluation package and bounded topology-group weighting. The paper should avoid first-ever language and acknowledge that external published methods were not fair drop-in comparators under the frozen contract.
""")
    write("paper/q2_draft/08_conclusion.md", """# 8. Conclusion

We studied heterogeneous UAV coordination when a Relay failure reorganizes legal communication and task-support paths. DRTP-SG-MAPPO preserves the matched Single-Graph MAPPO architecture and changes only the training distribution over predefined topology-perturbation groups. The historical evidence shows substantial average and median robustness gains across F0 and OOD conditions, but it also shows meaningful sensitivity to training initialization, including an adverse held-out seed and non-uniform safety outcomes.

The appropriate conclusion is therefore bounded: DRTP is a high-upside, seed-sensitive topology-perturbation training strategy for the studied three-UAV setting. It is not a universally stable or guaranteed robust method. Reporting the full seed distribution, absolute performance, safety, exposure validity, and topology/path mechanism is essential for making that conclusion reproducible.
""")
    print(json.dumps({"main_rows": len(rows), "seed_rows": len(raw), "decision": "A", "training_started": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
