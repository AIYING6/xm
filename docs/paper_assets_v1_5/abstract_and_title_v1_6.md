# Abstract versions & title candidates — v1.6 (journal-agnostic)

- status: claims frozen (paper-v1.6-p2-aligned); these are presentation variants only.
- hard constraints (both versions):
  - early-recovery vs MAPPO is the most reproducible evidence (RMST 50/80/100, 3 seeds
    same direction, bootstrap CI excludes 0);
  - full-horizon vs HAPPO / wider single-graph is **competitive**, never "faster/better";
  - NO conditional-time percentage headline (no 34%/38%/59%); conditional t_rec only as
    a named quantity ("conditional mean recovery time among recovered failure-exposed episodes").

## 1. Canonical abstract (~230 words; science master; in main.tex)

Heterogeneous UAV teams operating under incomplete sensing and degraded communication may
lose task-chain functionality after a critical node failure. This work therefore studies
post-failure recovery dynamics rather than terminal task success alone. We propose
EA-RG-MAPPO-S, a task-graph-driven multi-relation coordination method for 3DOF
heterogeneous UAV cooperative interception. The method represents perception,
communication, and task-dependent support relations in a multi-relation graph and
processes them using state-dependent, edge-feature-modulated attention under centralized
training and decentralized execution. A structured Gate Prior is further introduced to
improve the optimization stability of role-pair modulation. On a locked three-seed
held-out evaluation comprising 10,800 episodes, EA-RG achieves a post-failure recovery
rate of 0.971 ± 0.021. Censor-aware survival analysis on scenarios with matched failure
exposure yields an RMST of 14.47 ± 3.10 steps at the primary horizon of τ = 220, compared
with 20.39 ± 7.72 for MAPPO, 14.14 ± 2.94 for HAPPO, and 16.49 ± 8.64 for a wider
single-graph baseline. The full-horizon results therefore indicate competitive rather than
uniformly superior recovery. The most consistent advantage appears during early recovery:
at τ = 80, corresponding to the active node-failure interval, EA-RG reduces RMST from
15.51 steps for MAPPO to 11.81 steps, with all three training seeds showing the same
direction of improvement; the same pattern is observed at τ = 50 and 100. Ablation and
mechanism analyses further show that the Gate Prior improves optimization stability,
Task-Support provides an empirical relational benefit, whereas static Role-Pair Modulation
has limited independent benefit. These results indicate that task-graph multi-relation
coordination primarily improves the temporal concentration of early post-failure recovery
while maintaining high terminal reliability.

## 2. Short abstract (~170 words; claim-equivalent; for word-limited venues)

Heterogeneous UAV teams may lose task-chain functionality after a critical node failure.
We study post-failure recovery dynamics rather than terminal success alone and propose
EA-RG-MAPPO-S, a task-graph-driven multi-relation coordination method for 3DOF
heterogeneous UAV cooperative interception. It encodes perception, communication, and
task-support relations in a multi-relation graph processed by state-dependent,
edge-feature-modulated attention, with a structured Gate Prior for optimization stability.
On a locked three-seed held-out evaluation (10,800 episodes), EA-RG reaches a post-failure
recovery rate of 0.971 ± 0.021. Censor-aware survival analysis under matched failure
exposure gives a primary RMST of 14.47 ± 3.10 steps at τ = 220, versus 20.39 for MAPPO,
14.14 for HAPPO, and 16.49 for a wider single-graph baseline: full-horizon recovery is
competitive rather than uniformly superior. The most reproducible benefit is early
recovery relative to MAPPO: at τ = 80, the active node-failure interval, RMST drops from
15.51 to 11.81 steps with all three seeds in the same direction (also at τ = 50 and 100).
Gate Prior improves optimization stability and Task-Support gives an empirical relational
benefit, while Role-Pair Modulation has limited independent benefit. EA-RG thus shifts
post-failure recovery toward the early window while maintaining high terminal reliability.

## 3. Title candidates (frozen; final choice deferred to P2.6)

1. (recommended) **Task-Graph-Driven Multi-Relation Coordination for Early Post-Failure
   Recovery in Heterogeneous UAV Cooperative Interception** — matches the adjudicated
   evidence (early-window advantage); "Early" is precise.
2. (most conservative) **... for Post-Failure Recovery in Heterogeneous UAV Cooperative
   Interception** — no time adjective; least reviewer risk.
3. (current, backup) **... for Fast Post-Failure Recovery ...** — kept only as fallback;
   "Fast" can be challenged by the full-horizon HAPPO/wider-SG competitiveness.

## 4. Claim-equivalence check (both abstracts)

- [x] early-recovery vs MAPPO = most reproducible (RMST 80 = 11.81 vs 15.51, 3 seeds)
- [x] full-horizon vs HAPPO/wider SG = competitive (14.47 vs 14.14 / 16.49)
- [x] no conditional-time percentage headline
- [x] conditional t_rec named only as "conditional mean recovery time" (in body, not headline)
- [x] component verdicts: Gate Prior stability / Task-Support empirical / RPG limited
