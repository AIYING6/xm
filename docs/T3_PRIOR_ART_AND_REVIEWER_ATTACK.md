# T3 — Prior-Art Attack and Reviewer Stress Test

## Scope

This is a primary-source positioning audit, not a claim of novelty. It tests the strongest plausible T3 proposal—an actor-legal temporal task-support continuity belief—against existing work before implementation.

## Closest methods

| Method | What it infers/models | Temporal? | Graph? | Task semantics? | Actor legal? | Key difference / reviewer relevance |
|---|---|---:|---:|---:|---:|---|
| [TarMAC (ICML 2019)](https://proceedings.mlr.press/v97/das19a.html) | targeted messages and recipients | multi-round | implicit communication attention | downstream task only | decentralized at execution | Already learns targeted, multi-round communication in partially observed MARL. |
| [SARNet (NeurIPS 2020)](https://proceedings.neurips.cc/paper/2020/hash/72ab54f9b8c11fae5b923d7f854ef06a-Abstract.html) | memory-based attention over received information | yes | relational attention | cooperative communication | intended decentralized use | Directly weakens a memory-plus-relation novelty claim. |
| [Belief Representations (ICML 2023)](https://proceedings.mlr.press/v202/wang23p.html) | compact belief state from history with training-time state information | yes | no | reward-relevant representation | deployment history only | General precedent for training-only supervision of an execution-time belief. |
| [TGCNet (AAAI 2025)](https://ojs.aaai.org/index.php/AAAI/article/view/34507) | dynamic directed communication graph and execution features | yes (Transformer) | dynamic directed graph | cooperative task | explicitly studies execution communication | Makes dynamic topology plus graph modeling alone non-distinct. |
| [GA-MATR (2024)](https://arxiv.org/abs/2401.17880) | graph attention and graph recurrence for UAV communication topology | yes | yes | UAV communication/resource task | actor/critic architecture | Direct UAV precedent for graph-recurrent topology processing. |

Additional relevant work includes [IMAC (ICML 2020)](https://proceedings.mlr.press/v119/wang20i.html), which learns compact informative communication and scheduling, and [dynamic graph communication with node failures](https://arxiv.org/abs/2501.00165), which combines recurrent graph message passing with dynamic-network failures.

## Reviewer attack

### Reviewer A — MARL: “This is recurrent MAPPO plus an auxiliary classifier.”

**Attack succeeds.** A recurrence `b_i^t=F(b_i^{t-1},o_i^t,G_i^t)` trained to predict future availability is structurally a recurrent latent with an auxiliary predictive target. T3 finds no material history gain (+0.0083 AUC at best, negative by `L=16`), so a label name does not create a mathematical distinction from established memory/belief methods.

### Reviewer B — graph learning: “The graph part is ordinary temporal message passing.”

**Attack succeeds.** The actor-legal graph-history representation scores 0.9187 at `L=16`, below instantaneous observation (0.9248). T3 therefore identifies no graph-temporal information bottleneck that a new graph-state mechanism solves. Dynamic-graph and UAV graph-recurrent prior work also makes a topology-only distinction inadequate.

### Reviewer C — UAV/control: “M2 association cannot justify an algorithm.”

The permitted response would be limited: M2 identifies an associated capability deficit, not that a continuity state causes success. A later algorithm could be assessed by ablations, but T3 does not reach that point because the prerequisite—incremental temporal/graph identifiability—fails. Claiming a topology-continuity controller now would overstate the evidence.

## Prior-art outcome

No structural distinction stronger than “SG plus recurrent/history encoder plus predictive auxiliary loss” survives both the literature attack and the offline test. The correct action is not to rebrand generic memory as a new topology-support state.
