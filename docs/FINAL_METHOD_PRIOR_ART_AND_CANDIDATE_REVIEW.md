# Final Method Prior-Art and Candidate Review

**Status:** completed — paper-only screening; no implementation or training
**Decision:** no candidate family survives the combined evidence, legality, novelty, and stability screen.

## 1. Screening rule

A candidate must target a measured UTR-SG deficit, preserve the frozen actor boundary, possess a mechanism distinguishable from existing work, and pass all candidate-specific zero-training tests. A possible performance improvement is not enough. The program prohibits treating an application-only combination of GAT/MAPPO, recurrence, gating, gradient surgery, extra loss, parameter growth, or adaptive sampling as a final method.

## 2. Prior-art matrix

The following sources were reviewed as primary proceedings, official publisher pages, or preprints where a peer-reviewed page was unavailable. Mechanism descriptions are intentionally conservative.

| Work | Problem | Core mechanism | Inputs / objective | Graph or communication treatment | Failure relevance | Consequence for this project |
|---|---|---|---|---|---|---|
| [Gilmer et al., MPNN, 2017](https://proceedings.mlr.press/v70/gilmer17a/gilmer17a.pdf) | Graph learning | message/update/readout framework | node/edge attributes | general edge-aware message passing | none | Edge-conditioned aggregation is foundational, not a final novelty. |
| [Veličković et al., GAT, 2018](https://arxiv.org/abs/1710.10903) | Graph attention | learned neighbor attention | node features | attention over local neighbors | none | Replacing/augmenting attention alone is insufficient. |
| [Sukhbaatar et al., DIAL/RIAL, 2016](https://proceedings.neurips.cc/paper/2016/file/c7635bfd99248a2cdef8249ef7bfbef4-Paper.pdf) | Learning communication in MARL | differentiable/discrete communication learning | agent observations/reward | learned messages | indirect | Generic communication learning is not a distinctive relay-failure mechanism. |
| [Singh et al., IC3Net, 2019](https://openreview.net/pdf?id=rye7knCqK7) | Multi-agent cooperation | gated communication with individual/global control | agent hidden state | learned communication gating | partial observability | Independent gates are already known and were screened out by EDR. |
| [Jiang & Lu, ATOC, 2018](https://proceedings.neurips.cc/paper/2018/file/6a8018b3a00b69c008601b8becae392b-Paper.pdf) | Selective coordination | attention communication group formation | local observations | attention-based communication | indirect | A new attention/coordinator branch would be an existing-module substitution. |
| [Rong et al., DropEdge, 2020](https://arxiv.org/abs/1907.10903) | GNN robustness/over-smoothing | stochastic edge removal | graph adjacency | graph regularization | structural perturbation | Training-time edge dropout is not a specific legal topology-reconfiguration solution. |
| [Jin et al., Certifiable Robustness to Graph Perturbations, 2020](https://arxiv.org/abs/2008.10715) | GNN structure robustness | certificates against edge perturbations | graph structure | robustness bounds | structural attacks | A certificate would not establish a MARL coordination mechanism or solve seed instability. |
| [Morris et al., Universally Expressive Communication in MARL, 2022](https://proceedings.neurips.cc/paper_files/paper/2022/hash/d8a19c815a8bef25e6094e87f963d28e-Abstract-Conference.html) | communication expressivity | identifiers/noise for expressive GNN communication | agents/messages | expressive communication architecture | not relay-specific | Expressivity alone lacks an observed insufficiency and risks illegal identity/global shortcuts. |
| [Kao et al., 2022](https://proceedings.mlr.press/v151/kao22a.html) | Decentralized partial observability | approximate common-information state representation | local/common histories | belief/common-state compression | partial observability | A belief/history method is established; current logs do not demonstrate a legal instantaneous-state aliasing target. |
| [Chen et al., 2023](https://proceedings.mlr.press/v202/chen23an.html) | Context-aware MARL | Bayesian-network actor-critic contextual structure | contextual agent variables | structured critic/actor reasoning | nonstationarity | A context model needs a demonstrated, legal contextual variable beyond current features. |
| [MAGEC, 2024 preprint](https://arxiv.org/abs/2403.13093) | MARL under limited communication/agent attrition | GNN-MAPPO, edge attributes and selection | graph/edge attributes | graph message routing | close attrition setting | Existing edge-aware GNN-MAPPO is already close; a minor relation/reliability extension would face strong novelty attack. |
| [Dynamic directed graph communication, 2024 preprint](https://arxiv.org/abs/2408.07397) | cooperative communication | dynamic directed graph / transformer communication | agent states | learned communication graph | dynamic topology | New topology-learning would alter the frozen physical/legal graph problem. |
| [Graph MARL for collaborative UAV search/tracking, 2025](https://www.sciencedirect.com/science/article/pii/S1000936124003510) | UAV cooperative tracking | GAT-MARL | UAV graph states | graph-attentive MARL | dynamic UAV task | “GNN + MAPPO + UAV” cannot be the contribution. |
| [Yang et al., Communication-Constrained Priors, 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/e26502ce357ce3015e8778f0e85d4b39-Abstract-Conference.html) | communication-constrained MARL | lossy/lossless communication priors and dual mutual-information objective | messages/prior conditions | explicitly models communication reliability | close reliability treatment | A reliability-aware auxiliary objective is crowded and violates the “no generic loss” rule without a measured target. |
| [DIMA, 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/5e85dc044c7e774ebc1ce44963b4755c-Abstract-Conference.html) | MARL with dependent agents | diffusion world model | trajectories/dependencies | predictive generative modeling | nonstationary structure | World-model topology prediction is a high-compute, already-active family; current data lack a falsifiable prediction target. |

## 3. Candidate-family screen

### C1 — Relation/reliability-conditioned edge semantics

**One sentence:** Existing SG allegedly conflates a legal topology edge’s role and reliability; a condition-aware message would transform each local edge message based on relation/cache/link state.

**Evidence result:** rejected. Current edge features already include legal perception/communication/task-support indicators, distance/geometry, age, confidence and communication state. UTR residual telemetry does not isolate message-semantic conflation. Edge-aware GNN-MAPPO and communication-reliability priors are close prior art.

**Stress tests:**

- Remove-the-module: fails—ordinary edge features plus GAT remain the same basic story.
- Existing-method substitution: fails—an edge MLP/bias/gate/attention substitute reproduces it.
- UAV-removal: fails—without the task-specific evaluation it is merely edge-conditioned GNN-MARL.

### C2 — Legal temporal/belief topology representation

**One sentence:** Current snapshots allegedly cannot distinguish states requiring different legal reconfiguration actions; a history-derived belief would resolve that ambiguity.

**Evidence result:** rejected. Partial observability is plausible, but the allowed records contain episode aggregates, not aligned legal observation histories demonstrating same-current-observation/different-optimal-action aliasing. A simple GRU/LSTM is explicitly prohibited; a novel belief object has no observed target and is close to common-information/belief MARL.

**Stress tests:**

- Candidate-specific history-information test: **INCONCLUSIVE**, not PASS—no available trajectory-level legal-history target demonstrates incremental predictability.
- Existing-method substitution: fails—ordinary recurrence provides the same claimed remedy.
- Stability: high risk—new recurrent state introduces untested seed/buffer/normalization sensitivity.

### C3 — Topology-consequence predictor / world-model structural planning

**One sentence:** A predictor would forecast locally observable consequences of a relation switch and inform action selection before/after the relay failure.

**Evidence result:** rejected. Current telemetry does not contain an offline, causally useful next-topology or outcome target that can be predicted from the actor’s legal state, nor evidence that prediction—not policy quality—is the bottleneck. This would add auxiliary supervision and a world-model family already active in MARL.

**Stress tests:**

- Observable/predictable/non-redundant test: **INCONCLUSIVE** because only aggregate records are present.
- Actor legality: likely constrained; global route/failure truth cannot be a target leaked to execution.
- Compute/stability: high risk due to an added predictive objective and potential auxiliary-task domination.

### C4 — Communication–task multi-relation decomposition

**One sentence:** Separate relation channels would avoid coupling perception, communication, and task support in a merged graph.

**Evidence result:** rejected. This is directly contradicted by the historical Full/RSG screens: multi-relation branches and relation-aware variants did not establish nominal competence or robustness. Current graph fields already expose relation semantics. Reviving decomposition would reopen a closed evidence path without a new causal observation.

### C5 — Learned topology selection/control

**One sentence:** The policy could choose which topology/message edges to use under failure.

**Evidence result:** rejected. The core experimental object is a legal physical communication/task graph determined by sensing, range, delivery and failure semantics. Learning to alter it changes the frozen scientific question, risks bypasses/privileged graph truth, and is close to dynamic communication graph literature.

## 4. Candidate-specific zero-training falsification ledger

| Test | Data / code examined | Result | Consequence |
|---|---|---|---|
| Existing local-edge sufficiency | `_get_obs`, `_get_graph_obs`, current SG GAT; frozen information contract | **FAIL** for C1 premise | No evidence that a legal local relation/reliability variable is missing. |
| UTR topology telemetry association | 6,000 UTR final rows across five seeds/twelve conditions | **FAIL** as causal mechanism test | Task support/path switching correlate with return but do not identify a representation defect. |
| F0 learnability upper bound | Phase-FL specialist results | **FAIL** for “failure is intrinsically unlearnable” premise | F0 can be learned by a specialized SG policy; a universal robust-loss/predictor rationale is unsupported. |
| Legal history ambiguity/incremental prediction | available archive records/checkpoints | **INCONCLUSIVE** | No sequence-level legal-state target exists to validate C2/C3 without new instrumentation; an inconclusive core assumption cannot pass. |
| Structural aggregation novelty | EDR feasibility review and current GAT algebra | **FAIL** | Gated/residual/normalization/independent aggregation are existing mechanisms and EDR is closed. |
| Stability mechanism localization | DRTP/TCR forensic logs/runtime/projection/PPO telemetry | **FAIL** | Neither adaptive weighting nor one-sided projection yields an actionable causal target; adding feedback is disallowed. |

Under the program, any core-claim `FAIL` rejects the candidate. An `INCONCLUSIVE` core premise is also insufficient for `STRONG_GO_FINAL_METHOD` because training would be the first test of the mechanism.

## 5. Strong reviewer attacks

| Reviewer | Strongest rejection argument | Audit response | Outcome |
|---|---|---|---|
| R1, MARL | “This is MAPPO plus an existing communication/recurrent/predictive/gradient module; the chosen mechanism is not diagnosed from the task.” | Correct for C1–C5: no candidate establishes a measured, method-specific bottleneck. | Reject all candidates. |
| R2, graph learning | “Edge features, typed relations, attention, gates, normalization and message selection are standard; where is the structural property unavailable to ordinary edge-aware MPNNs?” | Current graph already has legal relation/cache/confidence features; EDR found no new independent structural novelty. | Reject C1/C4/C5. |
| R3, UAV/control | “Does the method actually respect decentralized information and solve a physical topology problem rather than use failure/global-route labels?” | A legal actor boundary can be preserved only by not adding privileged future/global topology. Candidate C3/C5 have no demonstrated legal target. | Reject C3/C5. |

## 6. Stability FMEA for the only plausible families

| Failure mode | Cause | Observable signature | Pre-training mitigation available without altering method | Residual risk |
|---|---|---|---|---|
| Adaptive feedback bifurcation | return/EMA/difficulty affects future exposure | seed-local sampling concentration or late collapse | avoid adaptive sampling; already frozen for UTR | Does not produce a new algorithm. |
| Gradient competition | nominal/failure objective interference | divergent seed, projection/cosine changes | avoid gradient surgery; TCR closed | No alternative causal mechanism observed. |
| Representation collapse / scale imbalance | extra branches, relation fusion, auxiliary heads | low nominal competence, branch dominance | avoid multi-branch/auxiliary structures | Prevents C1/C4/C3 rather than validates a replacement. |
| Shortcut / privileged conditioning | failure label, global route, future topology | actor changes under hidden-state interventions | strict information-boundary regression | C3/C5 cannot justify execution target. |
| Temporal state overfit | recurrent hidden state exploits train topology patterns | train/OOD divergence, seed dispersion | no evidence-based state abstraction or legal ambiguity test | High; C2 rejected. |
| Condition overfitting | predictive/auxiliary target tied to seen failures | high F0 but weak timing/duration/compound worst | fixed OOD evaluation only after training | High; no prior offline support. |

The historical DRTP/TCR failures make the residual risks unacceptable for a speculative architecture.

## 7. Result-free paper-worth simulation

No candidate satisfies the conditions for a candidate dossier, title, abstract, or algorithm contribution. Any proposed result-free abstract would necessarily depend on a hoped-for performance advantage rather than a method property already distinguished from prior work. Therefore the question “would stable, moderate gains alone yield a complete paper?” is answered **no** for C1–C5.

## 8. Review conclusion

The project has a defensible systems question and a reusable development comparator, but this screen found no sole final algorithm whose mechanism is simultaneously evidence-driven, legal, novelty-defensible, offline-falsified, and stability-credible. The correct action is to preserve R1 and stop algorithm invention at this point.
