# Scientific Integrity Hardening Audit

- status: **P0 HOLD — AUTHOR_DECISION_REQUIRED**
- date: 2026-08-08
- scope: locked `survival-protocol-v1.1` primary population, execution-time information boundary, metric estimands, and Gate Prior provenance.
- audit rule: this document reports code and frozen row-level evidence only. It does not alter the manuscript, figures, trained checkpoints, or numerical results.

## Executive finding

Two manuscript-level claims are not supported by the present implementation and locked primary data:

1. The primary Kaplan–Meier/RMST endpoint is **time to first stable task-chain establishment after failure onset**, not recovery of a task chain known to have been disrupted by that failure.
2. The code implements centralized construction and batch delivery of a whole graph to the actor. Relation masks constrain graph aggregation, and target state is zero-masked under the strict sensing setting, but the repository does **not** establish a per-UAV distributed graph-construction/execution realization. The current unqualified `CTDE / decentralized actor / local graph` wording is therefore unsupported.

The locked RMST values remain valid for the endpoint actually computed. They must not continue to be interpreted as evidence of post-disruption recovery unless a new, valid recovery protocol is established.

## A. Primary endpoint audit — P0

### A1. Code definition

In `scripts/evaluate_ri_gmappo_3d.py:233–260`, the evaluator scans from `node_failure_start_step` and sets `post_failure_chain_recovered=1` at the first later `chain_closed` step. Its time is the beginning of the four-step confirmation window:

\[
T = \max\{t_f, t_{\mathrm{first\;chain}}-h+1\}-t_f,\qquad h=4.
\]

The environment defines `chain_closed` in `envs/uav_intercept_3d_env.py:296–303` as four consecutive steps satisfying: an attack window is present, at least one blue actor tracks the target, and `_comm_has_chain_to_attacker()` is true. The relay failure is active only on the configured interval (`uav_intercept_3d_env.py:572–578`).

The evaluator separately records `post_failure_chain_recovered_after_loss`, but this condition is **not** the event used by `survival-protocol-v1.1` or by the RMST generator (`_operator_scripts/run_survival_v1_1.py:31–40`).

### A2. Locked row-level result

Audit source: `D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/formal_held_out_v1_5_10800_20260807/held_out_v1.5/{method}/seed{0,1,2}/test_episode_metrics.csv`. Population: frozen Early + Nominal, 600 failure-exposed episodes per method.

| Method | n | Maintained through failure | Reclosed after an observed post-failure loss | First established after failure | Unrecovered | Collision | Constraint violation | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EA-RG Full | 600 | 0 | 0 | 589 | 11 | 0 | 0 | 11 |
| MAPPO | 600 | 0 | 0 | 587 | 13 | 0 | 0 | 13 |
| HAPPO | 600 | 0 | 0 | 600 | 0 | 0 | 0 | 0 |
| Wider Single-Graph | 600 | 0 | 0 | 600 | 0 | 0 | 0 | 0 |
| w/o Gate Prior | 600 | 0 | 0 | 496 | 104 | 1 | 0 | 103 |
| w/o Task-Support | 600 | 0 | 0 | 554 | 46 | 1 | 0 | 45 |
| w/o Role-Pair Modulation | 600 | 0 | 0 | 598 | 2 | 0 | 0 | 2 |
| No Graph | 600 | 0 | 0 | 546 | 54 | 0 | 0 | 54 |
| Single Graph | 600 | 0 | 0 | 442 | 158 | 0 | 0 | 158 |

Thus **0/5,400** primary events across all nine frozen methods are recorded as a reclosure after an observed loss. In particular, the P1 EA-RG–MAPPO comparison is 589 vs 587 first establishments after failure, with no observed recovery-after-loss events for either method.

### A3. Consequence and viable author choices

- **Choice A — evidence-preserving reframe (no retraining):** rename the endpoint and paper around *post-failure stable task-chain establishment under an active relay failure*. Remove all assertions that the failure first breaks an already established chain, that a chain is reconfigured after disruption, or that a recovery event has been observed. RMST80 can remain, with its existing numeric values and comparison ceiling.
- **Choice B — retain a recovery paper:** require a revised scenario/protocol in which a stable pre-failure task chain is established and then objectively lost at failure onset, followed by a prospectively defined reclosure endpoint. The current frozen primary data cannot supply this endpoint; new evaluation and likely retraining would need a separately approved plan.

No manuscript wording can turn the present first-establishment endpoint into recovery evidence. The audit does not choose between A and B for the authors.

## B. Execution-time information boundary audit — P0

### B1. What is protected

- Individual local observations in `envs/uav_intercept_3d_env.py:930–1027` gate target state by a local target cache under strict sensing.
- The graph target node is zero-masked under strict target sensing plus the target-information bottleneck (`uav_intercept_3d_env.py:880–891`).
- Communication and task-support relation entries are constructed from environment-delivered communication; task support additionally requires role and information conditions (`uav_intercept_3d_env.py:1032–1143`, `1163–1175`).
- Both relation-specific attention and union-graph attention use adjacency matrices as hard masks (`algorithms/ri_gmappo/simple_ri_gmappo.py:172–249`).

These controls rule out the particular direct target-state leak that the graph constructor explicitly documents.

### B2. What is not established

`_get_graph_obs()` constructs a single graph containing every blue actor's position, velocity, detection flag, local attack-window flag, energy, and all pairwise edge features (`uav_intercept_3d_env.py:1032–1143`). Evaluation stacks that full graph and calls one actor batch (`scripts/evaluate_ri_gmappo_3d.py:493–508`); `RIActor` receives the full graph and produces all action logits (`algorithms/ri_gmappo/simple_ri_gmappo.py:591–616`).

There is no per-UAV graph constructor, no serialization/broadcast protocol, and no assertion that each actor receives only graph fields locally observable or delivered to it. Two masked graph-attention layers may propagate information along active multi-hop graph paths in a single forward pass. This may be an intended centralized graph computation, but it is not a demonstrated distributed realization.

| Input to actor graph | Source in current implementation | Can the code establish per-UAV local availability? |
|---|---|---|
| Blue positions, kinematics, energy, detection and local-window flags | Environment arrays for **all** blue actors | No |
| Target node state | Zero-masked under strict sensing/bottleneck | Yes for the target-state mask only |
| Communication relation | Environment-delivered adjacency | Edge validity yes; distributed graph assembly no |
| Task-support relation | Role, delivered communication and information conditions | Edge validity yes; distributed graph assembly no |
| Pairwise edge features | Full pairwise environment geometry/state arrays | No |
| Critic shared state | `_get_share_obs()` global state | Yes, critic-only as coded |

### B3. Consequence and viable author choices

- **Choice A — evidence-preserving reframe:** describe the implemented policy as a *centralized graph-conditioned coordinated policy with per-actor action outputs*. Retain the CTDE training fact only where exact, and remove claims of decentralized execution, local graph construction, or deployable communication-limited realization.
- **Choice B — retain decentralized-execution claims:** implement and validate per-UAV graph construction/access control, then rerun the affected training/evaluation evidence under that implementation. This requires an approved scientific expansion.

## C. Censoring and termination audit — Conditional repair

For the frozen P1 population, EA-RG and MAPPO have zero collisions and zero constraint violations; their only non-events are timeouts (11 and 13, respectively). The evaluator censors an unrecovered episode at `steps − failure_start`, i.e., at its actual terminal follow-up (`scripts/evaluate_ri_gmappo_3d.py:257–261`; `_operator_scripts/run_survival_v1_1.py:31–40`).

Accordingly, the manuscript/protocol must say **right-censored at observed episode termination (or administrative horizon when reached)**. `survival_protocol_v1_1.md` currently says “collision: primary = horizon censoring”, which is not the generator's general rule and must be corrected if the paper proceeds. The collision statement is immaterial to the EA-RG–MAPPO P1 point comparison but cannot remain as an implementation description.

## D. Metric-estimand repair — Conditional repair

If the authors select an evidence-preserving reframe, Table 1 should be rebuilt around explicit estimands:

| Quantity | Population | Treatment of non-event/termination | Status |
|---|---|---|---|
| Terminal task-chain establishment / success | locked held-out suite; three training seeds | terminal descriptive proportion | descriptive only |
| Conditional time to first post-failure stable chain | failure-exposed episodes with an observed stable chain | excludes non-events; never replaces RMST | descriptive only |
| RMST80 / RMST220 | Early + Nominal; 200 matched failure-exposed episodes per seed, 600 per method | right-censored at observed termination / horizon | primary time endpoint (with renamed event) |

The existing frozen `sensitivity_rmst.csv` supports reporting RMST80 point estimates for all four main-table methods: EA-RG 11.81, MAPPO 15.51, HAPPO 13.52, Wider Single-Graph 13.84 steps. Only the predeclared EA-RG–MAPPO RMST80 comparison should retain inferential emphasis.

## E. Gate Prior provenance — Conditional repair

The code initializes selected role-pair gates with fixed `role_gate_prior_strength=0.4` (`configs/paper/ea_rg_mappo_gate_prior.yaml:14`; `simple_ri_gmappo.py:294–326`). It is a static initialization and not an input-dependent, online gate. Repository evidence currently verifies the fixed value and its mappings, but does not document why 0.4 was selected or a sensitivity study. If the paper proceeds, describe it only as a fixed pre-training configuration and do not claim hyperparameter-independent effect or optimally selected strength.

## Required author decision

Before any manuscript revision or fresh reviewer simulation, select one consistent pair:

1. **Reframe now, no new experiments:** (i) post-failure first stable-chain establishment; (ii) centralized graph-conditioned coordinated action outputs.
2. **Retain the present recovery/decentralized claims:** approve the necessary new scenario/protocol, distributed-input implementation, and rerun plan.

Until that choice, `SUBMISSION_READY_INTERNAL` remains prohibited. The previously frozen figures may remain visually frozen, but their captions and scientific interpretation cannot be frozen under the current wording.
