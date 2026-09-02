"""Generate the zero-training master design audit for the redundant-topology UAV project.

This script is deliberately static: it imports no environment or learner and creates no
rollout, seed, checkpoint, or evaluation artifact.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "configs" / "master_design_p0_20260902.json"
OUT = ROOT / "docs" / "master_design_p0_20260902"


def write(name: str, body: str) -> None:
    (OUT / name).write_bytes((body.strip() + "\n").encode("utf-8"))


def main() -> None:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = {
        "A": (1, 2, 1, "Conservative"),
        "B": (2, 2, 2, "Recommended"),
        "C": (2, 3, 3, "Ambitious"),
    }
    rows = []
    for key, (s, r, t, label) in candidates.items():
        paths = s * r * t
        edge_disjoint = min(s * r, r * t)
        internal_node_disjoint = r
        rows.append((key, label, s + r + t, paths, edge_disjoint, internal_node_disjoint))

    contract = """
# MASTER_DESIGN_P0 contract

**Protocol:** `MASTER-DESIGN-P0-ZERO-TRAINING-V1`  
**Scope:** static scientific and engineering design only.  
**Status:** complete; P1 is not authorized.

This audit creates a separate future benchmark namespace, `redundant_topology_uav`, and preserves the frozen 3-UAV Scout--Relay--Attacker A-line unchanged. It performs no environment import, modification, rollout, policy evaluation, new-seed creation, hyperparameter sweep, or training.

The P0 decision is intentionally narrower than a research claim: the layered redundant-topology question is justified, but the present 3-UAV implementation is not a scalable generator and cannot be repurposed without a new semantic specification. Therefore the only valid final verdict is `MASTER_DESIGN_REQUIRES_REDESIGN`.

## Non-negotiable future gates

1. Prove actor-side task-information legality for every nominal and failure graph.
2. Freeze role differentiation, success semantics, and normalized reward/metric definitions before implementation.
3. Implement a new generator in an isolated namespace; do not patch the frozen A-line environment.
4. Pass graph-equivalence, recoverability, information-boundary, smoke, and comparator-mapping gates before any learning experiment.
5. No candidate method is predeclared the winner; all training-distribution methods remain hypotheses.
"""
    write("MASTER_DESIGN_P0_CONTRACT.md", contract)
    write("FINAL_SCIENTIFIC_QUESTION.md", """
# Final scientific question

> **How should heterogeneous multi-UAV policies be trained to remain effective under structurally distinct and partially recoverable communication-topology failures?**

中文：在具有冗余任务信息路径的异构多无人机系统中，面对结构上真正不同且部分可恢复的通信拓扑故障，应如何设计训练分布，使策略兼顾任务性能、故障恢复、跨拓扑泛化和训练可靠性？

The benchmark—not a preselected DRTP variant—is the first contribution. UTR, original DRTP-style adaptive exposure, curriculum/prioritized exposure, robust/group training, and a future topology-aware candidate are competing answers. A later paper may claim performance, reliability, or stability only at the separately defined evidence levels.
""")
    write("CLAIM_EVIDENCE_MATRIX.md", """
# Claim--evidence matrix

| Claim | Required evidence before publication | Forbidden shortcut |
|---|---|---|
| Benchmark has real redundancy | actor-legal route proof, graph signatures, recoverability audit | drawing unused graph edges |
| Failures are structurally distinct | equivalence classes over task-relevant directed graph | relabeling timing as topology |
| Uniform exposure is not always optimal | matched UTR/plain/external comparisons at fixed budget | selecting a preferred seed/checkpoint |
| Candidate improves performance | fresh paired training seeds, fixed evaluation tape, nominal and recoverable metrics | treating evaluation episodes as independent training samples |
| Reliability improves | lower tail, catastrophic count, dispersion, separate cohorts | pooling cohorts to hide reversal |
| Generalization improves | pre-frozen held-out structures, structural OOD, scale protocol | inventing OOD after results |
| Stability is solved | multiple fresh cohorts at mature horizon plus held-out support | equating mean improvement with stability |
""")
    arch_rows = "\n".join(f"| {k} | {label} | {n} | {p} | {e} | {i} |" for k, label, n, p, e, i in rows)
    write("AGENT_ROLE_ARCHITECTURE_AUDIT.md", f"""
# Agent-role architecture audit

All candidates use a directed layered task-support family `Scout -> Relay -> Terminal`. A path is only potential until a future semantic contract proves that its source information, relay forwarding and terminal action are needed by the task.

| Design | role composition | UAVs | legal potential paths | edge-disjoint route capacity | internally node-disjoint routes |
|---|---|---:|---:|---:|---:|
{arch_rows}

| Design | scientific richness | topology diversity | recoverability | scalability | implementation risk | training cost | external validity | paper ceiling |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: 1S+2R+1T | 3 | 3 | 3 | 2 | 5 | 5 | 3 | 3 |
| **B: 2S+2R+2T** | **5** | **5** | **5** | **4** | **3** | **3** | **5** | **5** |
| C: 2S+3R+3T | 5 | 5 | 5 | 5 | 2 | 1 | 5 | 5 |

## Recommendation

Select **B (6 UAV)** only after redesign: Scouts must have complementary sensing sectors/altitude/range, terminals must have complementary terminal capabilities or spatial responsibilities, and relays must be individually meaningful routing resources. If any duplicated role is interchangeable without changing task-information or mission semantics, B fails and must be redesigned rather than trained. A is a sanity scale; C is an eventual scale stress test, not the main formal scale.
""")
    write("REDUNDANT_PATH_GRAPH_DESIGN.md", """
# Redundant task-path graph design

## Frozen design direction

For main scale B, use the directed layered support graph:

```text
S1 ----> R1 ----> T1
 |        |        |
 |        v        v
 +------> R2 ----> T2
S2 ----> R1/R2 ----> T1/T2
```

Every `S_i -> R_j -> T_k` route is a candidate legal support path. The semantic design must require: (i) a scout observation not reconstructible by terminals alone, (ii) a relay-carried support message, and (iii) terminal action conditioned on legal, age-bounded support. Nominal B has eight directed routes, four relay-edge-disjoint branch pairs from the Scout layer to the terminal layer, and two internally relay-node-disjoint branches for a fixed source-terminal pair.

**Critical distinction:** this is not an approval to add graph edges. P1 must prove active use through actor observations, message provenance, cache-age legality and action/attack gating. Dynamic radio connectivity, dropout and policy behavior are secondary realizations of a frozen static task-support mask, never substitutes for the mask.
""")
    write("SCALE_FAMILY_SPEC.md", """
# Scale-family specification

| Scale | role counts | role in project | training interpretation |
|---|---|---|---|
| Small | 1S+2R+1T (4) | semantic smoke, visualization, ablation | independently trained |
| Main | 2S+2R+2T (6) | formal claims, external comparators, reliability | independently trained |
| Large | 2S+3R+3T (8) | scalability and structural stress | independently trained |

All scales must be emitted by one configuration-driven generator: role inventory, positions, directed support graph, per-role observation schema, failure masks, reward normalization and task-success contract. Cross-scale evaluation is optional and must be labeled zero-/few-shot only if it actually uses a model trained at another scale; it cannot be conflated with in-scale performance.
""")
    write("FAILURE_TAXONOMY_MASTER_SPEC.md", """
# Failure taxonomy master specification

Primary labels are topology structures; timing and duration are orthogonal factors.

| Structural class | Tier candidate | Definition | Main use |
|---|---|---|---|
| noncritical directed edge loss | R | one path edge removed; legal alternate route remains | main training/evaluation |
| relay ingress/egress partial loss | R/C | selected relay links removed | main / stress |
| single relay-node loss | R/C | all incident task-support links disabled | recovery stress |
| scout or terminal partial capability/link loss | R/C | role-specific support degradation | held-out family member |
| multi-edge redundancy loss | C | two non-cut edges jointly removed | critical stress |
| local-subnetwork degradation | C | correlated mask/dropout within one branch | structural OOD candidate |
| edge+node compound | C/I | composition classified by reachability | OOD / lower bound |
| cut-set / complete impossible topology | I | no legal source-to-terminal task path | impossibility reference only |

Each class later crosses `structure × onset {early,middle,late} × duration {short,medium,long}`. No timing/duration label may be reported as a new topology class.
""")
    write("FAILURE_EQUIVALENCE_AND_RECOVERABILITY_AUDIT.md", """
# Failure equivalence and recoverability audit

Before training, enumerate all masks allowed at each scale and calculate the task-relevant signature:

`(directed edge set, role-labelled degree vector, SCCs, legal reachability, path count, edge-disjoint count, internally-node-disjoint count, shortest legal route, cut edges/nodes, redundancy tier)`.

Masks with the same signature **and** same actor-observable/legal-action consequence are one condition; they are not duplicated as separate samples. A condition is Tier R only if at least one legal information route and a physically reachable success maneuver remain. Tier C has a route but low redundancy or tight message-age/rerouting margin. Tier I has no legal success route and is excluded from ordinary mean-performance comparisons.

Expected main-scale B target: at least five recoverable equivalence classes after symmetry collapsing, at least two critical classes, and at least one explicit impossible cut-set reference. Failure to meet three genuinely different recoverable classes is a benchmark stop/redesign gate.
""")
    write("TOPOLOGY_SEVERITY_AUDIT.md", """
# Topology severity audit

Severity is a descriptive structural stratifier, not a training-probability rule. First attempt only policy-independent quantities: legal path loss, residual edge-/node-disjoint redundancy, reachability loss, shortest-route increase and cut-set status. If one scalar does not preserve meaningful partial order, retain a multidimensional signature rather than inventing a weighted scalar.

No severity-to-sampling mapping is authorized by P0. A later candidate must justify any exposure prior independently of evaluation performance and compare it against uniform exposure.
""")
    write("INFORMATION_BOUNDARY_TABLE.md", """
# Information-boundary table

| Information | Actor at execution | Central critic during training | Trainer bookkeeping | Evaluation-only |
|---|---:|---:|---:|---:|
| own role/state and legal local sensing | yes | yes | yes | no |
| received timestamped/provenance-tagged messages | yes | yes | yes | no |
| support-link state observable locally | only if sensed/communicated | yes | yes | no |
| full topology mask / all agents' states | no | yes | yes | no |
| failure class, group id, curriculum probability | no | no unless inferable from allowed state | yes | no |
| seed, RNG streams, episode identifiers | no | no | yes | no |
| formal/held-out tape, aggregate scores, future labels | no | no | no | yes |

Actor messages require source, age, route/provenance and validity flags. The future environment must apply static failure masks before packet creation, cache update and graph construction; pruning an already-built adjacency is not adequate.
""")
    write("REWARD_AND_METRIC_REACHABILITY_AUDIT.md", """
# Reward and metric reachability audit

The existing 3-UAV reward cannot be copied mechanically: pairwise collision opportunities, connectivity averages and per-role bonuses change with N. P1 must define normalized quantities with invariant physical meaning.

| Quantity | required scale-safe definition | gate |
|---|---|---|
| mission progress | normalized target/intercept progress relative to scale-specific feasible geometry | attainable nominally |
| success | role-legal terminal neutralization under valid support path | feasible in R/C, impossible in I |
| collision | collision rate per UAV-pair exposure plus episode indicator | no automatic N penalty |
| communication | task-path availability/age, not dense all-pairs closure alone | respects directed support graph |
| role rewards | role-normalized contribution, bounded total magnitude | no reward inflation from copies |
| timeout | fixed physical mission deadline or normalized horizon | comparable within scale |

Before learner connection, deterministic scenario sweeps must establish reachable success, recoverable rerouting and impossible lower-bound semantics. This is a future design/smoke requirement, not a P0 experiment.
""")
    write("SG_MAPPO_SCALABILITY_AUDIT.md", """
# SG-MAPPO scalability audit

The graph-attention actor can process a fixed node count per vectorized batch and already uses role embeddings; it can support an in-scale configuration-driven N after environment generalization. The CTDE critic dimensions must be rebuilt from N and role inventory, and counterfactual action features scale with `N × action_dim`. A mixed-scale vectorized batch is unsupported without padding/masking; train/evaluate each scale separately first.

Required future changes are isolated to the new namespace: variable-N generator, role schema, configuration-derived shared observation dimensions, generalized failure sampling (the current legacy sampler assumes three agents), route-provenance features, and scale-aware metric normalization. No large algorithmic rewrite, new GNN family, or task-specific action hack is justified at P0. Parameter sharing is recommended within role type; role permutation augmentation/equivariant tests are mandatory when copies are symmetric.
""")
    write("EXTERNAL_COMPARATOR_NOVELTY_MAP.md", """
# External comparator and novelty map

The following mapping is a design audit, not an implementation claim. URLs are primary sources where available. Freeze one feasible curriculum/prioritized comparator and one feasible robust/group comparator before the first main-scale training.

| Work | problem / task distribution | update signal | policy-dependent | static/adaptive | topology-aware | MARL/UAV | failure type | complexity | fair mapping |
|---|---|---|---:|---|---:|---|---|---|---|
| Jiang et al., PLR (ICML 2021) | prioritize replayed levels | learning potential | yes | adaptive | no | RL / no | level difficulty | medium | yes: failure-mask replay |
| Portelas et al., teacher-curriculum survey | curriculum task selection | competence/progress | often | mixed | no | RL / no | task variation | medium | conceptual only |
| Klink et al., SPDL (ICLR 2021) | self-paced task distribution | performance/KL constraint | yes | adaptive | no | RL / no | domain parameters | high | partial |
| Mehta et al., ADR (CoRL 2020) | active domain randomization | policy boundary | yes | adaptive | no | RL / no | domain shift | high | partial |
| Dennis et al., PAIRED (NeurIPS 2020) | adversarial environment generation | regret | yes | adaptive | no | RL / no | generated levels | high | no: changes task generator |
| Rajeswaran et al., EPOpt (arXiv 2016) | robust domain distribution | worst percentile | yes | robust | no | RL / no | model variation | medium | yes: failure-group CVaR |
| Xu et al., GDR-RL (ICLR 2023) | group distributional robustness | group return | yes | robust | no | RL / no | group shift | medium | yes: frozen failure groups |
| Lowe et al., M3DDPG (AAAI 2019) | adversarial multi-agent robustness | adversary | yes | adaptive | no | MARL / no | adversarial policy | high | partial |
| Kim et al., ADMAC (AAAI 2024) | robust communication MARL | communication adaptation | yes | adaptive | yes | MARL / no | attacks/noise | high | partial |
| Li et al., Mis-Spoke or Mis-Lead (2021) | communication robustness | attacked messages | yes | static | yes | MARL / no | communication corruption | high | partial |
| Zhang et al., Certifiably Robust Policy Learning (2022) | robust decentralized communication | certificate/loss | yes | robust | yes | MARL / no | message attack | high | partial |
| MA3C (2023) | resilient communication | curriculum/communication state | yes | adaptive | yes | MARL / no | link disruption | high | partial |
| ExpoComm (ICLR 2025) | communication-efficient MARL | information budget | yes | adaptive | graph-aware | MARL / no | bandwidth | high | no: different objective |
| ETRI resilient UAV network (TNSM 2026) | UAV network resilience | routing/network control | mixed | mixed | yes | UAV | network failures | high | conceptual |
| UAV network restoration MARL (Ad Hoc Networks 2025) | restoration scheduling | task reward | yes | adaptive | yes | UAV | node/link outage | high | conceptual |

## Frozen mapping decision

**External curriculum/prioritized:** PLR-style failure-mask prioritization, adapted only after an offline mapping proof that its replay/update cadence does not grant extra data or privileged actor information.  
**External robust/group comparator:** EPOpt/CVaR-style or GDR-RL-style frozen failure-group objective; choose exactly one after interface audit.  
**Not fair as drop-in:** PAIRED, full ADR, most communication-defense methods and UAV network restoration papers alter the generator, adversary, network-control objective or information channel.

Sources: [PLR](https://proceedings.mlr.press/v139/jiang21b.html), [GDR-RL](https://proceedings.mlr.press/v206/xu23d.html), [SPDL](https://arxiv.org/abs/2004.11812), [ADR](https://arxiv.org/abs/2002.07911), [PAIRED](https://arxiv.org/abs/2012.02096), [EPOpt](https://arxiv.org/abs/1610.01283), [ADMAC](https://ojs.aaai.org/index.php/AAAI/article/view/29708), [Mis-Spoke](https://arxiv.org/abs/2108.03803), [Robust communication](https://arxiv.org/abs/2206.10158), [MA3C](https://arxiv.org/abs/2305.05116), [ExpoComm](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3514dbacaebf0f38b25adfe59ed81a8a-Abstract-Conference.html), [UAV restoration](https://doi.org/10.1016/j.adhoc.2025.103785).
""")
    write("OOD_AND_HELDOUT_CONTRACT.md", """
# OOD and held-out contract

| Partition | admissible structures | purpose | allowed use |
|---|---|---|---|
| training support | frozen Tier-R classes and timing/duration combinations | learner exposure | training only |
| development | disjoint members of same support family | implementation/method choice | development only |
| held-out | same family, unseen specific structural masks | standard generalization | final only |
| structural OOD | unseen edge compounds, node+edge compositions, redundancy tier and/or larger scale | structural transfer | final only |

All membership lists, evaluation seeds, scenario geometry and timing/duration combinations must be hashed before learner training. Held-out/OOD scores never choose a method, threshold, curriculum probability or checkpoint.
""")
    write("TELEMETRY_MASTER_SPEC.md", """
# Telemetry master specification

Record from the first learner run: role-labelled positions/actions; reward components; mission progress; success/collision/timeout; failure-relative time; static and active directed adjacency; connected components; legal task paths; residual redundancy; message age/provenance/dropout; route/path use, switching and rerouting latency; pre/post-failure degradation and recovery; sampled group/probability; actor loss, critic loss, KL, entropy and clipping.

Write typed, schema-versioned files at fixed intervals and at every failure event. Telemetry is training-only/diagnostic and must be default-off trajectory equivalent when disabled. Evaluation produces outcomes but cannot feed online controls.
""")
    write("RNG_AND_REPRODUCIBILITY_SPEC.md", """
# RNG and reproducibility specification

Freeze independent reproducible streams: `seed_init`, `seed_env`, `seed_action`, `seed_minibatch`, `seed_task`, `seed_failure`, `seed_comm`, `seed_topology`, and `seed_eval`. Record stream derivation, environment/config hash, code commit, hardware/software versions, topology/failure list hashes, checkpoint hash and evaluation-tape hash in every manifest. Save enough runtime state to resume exactly, including optimizer, sampler, RNG streams and message/cache state.
""")
    write("SEED_COHORT_CONTRACT.md", """
# Seed/cohort contract

Training seed is the independent unit; episodes, updates and cells are technical repetitions. Before training, allocate non-overlapping registries: development cohort for design, replication cohort for independent validation, confirmatory cohort for final claims, and evaluation-only seeds/tapes. Cohorts are reported separately; pooled estimates are secondary and never replace a reversal check. No seed replacement, performance rerun or best-checkpoint promotion.
""")
    write("TRAINING_BUDGET_PLAN.md", """
# Training budget plan

| Stage | purpose | indicative environment steps | stop rule |
|---|---|---:|---|
| semantic smoke | implementation only | <=1M total | graph/reachability failure |
| pilot | direction on fresh seeds | ~15M | no pre-frozen performance signal |
| development | select one candidate through development only | ~20M | weak or unsafe candidate |
| mature replication | separate two 5-seed cohorts at 2M | ~60M | cohort reversal |
| confirmatory | winner vs required comparators at 3M | ~90M | no Level-2 reliability evidence |
| OOD/scale/ablation | claim completion | ~25--50M | failed claim boundary |

Total full programme: approximately **210--236M environment steps**, plus fixed-tape evaluations. Estimate wall-clock only after an isolated main-scale throughput smoke test; a single 3080 Ti and 50 GB data disk are not adequate evidence for this full programme. Plan for staged cloud execution, checkpoint/telemetry compression, and at least several hundred GB of durable storage. Maximum concurrency is a hardware-calibrated safety parameter, never a scientific result.
""")
    write("GO_NO_GO_TREE.md", """
# GO/NO-GO tree

```text
Benchmark semantics and redundant legal paths valid?
├─ no  -> STOP / redesign benchmark
└─ yes
   ├─ failure equivalence has >=3 recoverable classes and clean R/C/I tiers?
   │  ├─ no  -> STOP / redesign graph
   │  └─ yes
   │     ├─ external comparators map fairly and information boundaries pass?
   │     │  ├─ no  -> redesign before learning
   │     │  └─ yes
   │     │     ├─ plain/UTR learns nominal and Tier-R task?
   │     │     │  ├─ no  -> environment/metric failure
   │     │     │  └─ yes
   │     │     │     ├─ one pre-frozen candidate passes pilot?
   │     │     │     │  ├─ no -> benchmark-only/negative-study decision; no blind tuning
   │     │     │     │  └─ yes
   │     │     │     │     ├─ independent cohort repeats Level-1/2 direction?
   │     │     │     │     │  ├─ no -> mixed-result claim only
   │     │     │     │     │  └─ yes -> confirmatory, OOD and scale evidence
```
""")
    write("FINAL_EXPERIMENT_MATRIX.md", """
# Final experiment matrix

| ID | experiment | evidence claim | mandatory comparator / endpoint |
|---|---|---|---|
| E1 | nominal performance | base competence | plain, UTR; success/mission score |
| E2 | recoverable topology failures | main robustness | all frozen methods; R-tier score/recovery |
| E3 | critical stress | graceful degradation | C-tier lower tail/safety |
| E4 | structure × timing × duration | factor separation | fixed factorial subset |
| E5 | held-out same-family masks | within-family generalization | no training exposure |
| E6 | structural OOD | topology generalization | unseen compounds/redundancy/scale |
| E7 | scalability | in-scale scale behavior | 4/6/8 separate training |
| E8 | safety | collision/timeout trade-offs | all methods |
| E9 | reliability | seed risk | two independent cohorts, lower tail/range |
| E10 | ablation | candidate causal components | default-off and component removal |
| E11 | external comparator | novelty positioning | PLR-style + robust/group method |
| E12 | cost | practical scaling | params, wall-clock, steps, telemetry/storage |
""")
    write("FINAL_FIGURE_TABLE_PLAN.md", """
# Final figure and table plan

Fig. 1 benchmark roles, legal information paths and actor boundary; Fig. 2 graph-equivalence failure taxonomy; Fig. 3 training-distribution framework; Fig. 4 main R-tier performance; Fig. 5 failure recovery trajectories; Fig. 6 held-out/structural OOD; Fig. 7 cohort reliability/lower-tail distribution; Fig. 8 scale/runtime; Fig. 9 performance--safety/reliability frontier.

Tables: (1) scenario/role parameters, (2) failure signatures and R/C/I tiers, (3) method-information/computation fairness, (4) main results with confidence and paired seed summaries, (5) safety/reliability, (6) OOD/scale/cost, (7) ablations. Every panel must identify the independent unit and whether it is development, replication or confirmatory evidence.
""")
    write("MANUSCRIPT_BLUEPRINT.md", """
# Manuscript blueprint

1. **Introduction:** structurally recoverable communication-topology failures create a training-distribution problem.
2. **Related work:** curriculum/prioritized RL, robust/group RL, communication-robust MARL and UAV resilience.
3. **Problem and information boundary:** roles, legal messages, CTDE boundary.
4. **Redundant-topology benchmark:** scale generator and reachability semantics.
5. **Failure taxonomy:** graph signatures, equivalence and R/C/I tiers.
6. **Training-distribution framework:** uniform, adaptive, external and candidate methods.
7. **Proposed method:** only after development evidence nominates one.
8. **Experimental protocol:** cohorts, fixed tapes, OOD, reproducibility.
9. **Main results:** E1--E4.
10. **Reliability and safety:** E8--E9, with limits rather than overclaim.
11. **Structural OOD and scalability:** E5--E7.
12. **Behavior/mechanism:** telemetry-backed route behavior, only if supported.
13. **Limitations and conclusion:** evidence-level calibrated.
""")
    write("PUBLICATION_EVIDENCE_LEVELS.md", """
# Publication evidence levels

| Level | permitted statement | required evidence |
|---|---|---|
| Minimum publishable | benchmark and one method show bounded, reproducible main-scale performance | semantic proof, UTR/plain, fresh pilot, safety |
| Strong application Q2 | candidate improves R-tier performance with credible reliability and held-out evidence | external comparators, separate replication cohort, OOD, scale/cost |
| Q1-level aspiration | broad, mature and robust conclusion | confirmatory cohorts, mature horizon, multiple scales/OOD, strong external methods |

Level 1 performance success (mean/median/majority/nominal/safety), Level 2 reliability improvement (catastrophe/lower tail/dispersion/cohort consistency), and Level 3 stability solved (multiple cohorts, mature horizon, held-out consistency) must remain separate throughout writing.
""")
    write("MASTER_RISK_REGISTER.md", """
# Master risk register

| Risk | prevention before training |
|---|---|
| graph too dense / failures irrelevant | legal-path and equivalence audit |
| graph too sparse / failures terminal | R/C/I reachability proof |
| duplicate roles | complementary sensing/terminal capability contract |
| reward scales with N | normalized reward/metric reachability gate |
| actor leakage | provenance/age boundary test |
| role permutation artifacts | sharing/equivariance test and canonical ordering |
| action/critic scaling | per-scale dimension and memory smoke |
| PPO instability | fixed-budget pilot and telemetry, no sweep |
| combinatorial failures | equivalence collapse and frozen subset |
| OOD leakage | hashed partitions before learning |
| unfair comparator | interface/cost/information mapping gate |
| topology metric detached from task | report signature descriptively; do not use as outcome proxy |
| novelty too weak | external map and candidate-free benchmark fallback |
| storage/compute shortfall | staged budget and durable-storage plan before P1 |
""")
    write("P0_FINAL_VERDICT.md", """
# P0 final verdict

## `MASTER_DESIGN_REQUIRES_REDESIGN`

The research question and a scalable layered redundant-topology benchmark family are justified. Candidate B (2 Scouts, 2 Relays, 2 terminal UAVs) is the best main-scale design **conditional on** proving non-duplicated roles and task-legal use of its redundant paths.

P0 cannot return READY because the current 3-UAV environment hardcodes three positions/kinematics, a required relay identity, legacy direct-recovery semantics, three-agent failure sampling, and reward terms whose meaning changes with agent count. The new generator, success semantics, role complementarity, normalized metrics, failure-mask ordering and durable compute/storage plan must be frozen before implementation.

**P1 is not authorized. No environment, training, rollout or evaluation was started.**
""")
    payload = {
        "protocol": cfg["protocol"], "authorization": cfg["authorization"],
        "recommended_design": {"name": "B", "roles": "2 scout + 2 relay + 2 terminal", "uavs": 6, "potential_paths": 8},
        "checks": {
            "scientific_question_justified": True, "redundant_path_family_defined": True,
            "current_legacy_environment_scalable": False, "future_semantic_contract_frozen": False,
            "comparator_plan_available": True, "ood_plan_available": True,
            "full_compute_requires_staged_cloud_and_storage": True
        },
        "verdict": cfg["final_verdict"], "next_step_authorized": False,
        "source_sha256": hashlib.sha256(CFG.read_bytes()).hexdigest()
    }
    (OUT / "MASTER_DESIGN_P0.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
