# PAPER-Q2 Reviewer Attack Response Plan

**Generated:** 2026-08-22. This is a response matrix, not a claim that the concerns are already solved.

| Likely reviewer attack | Evidence-based response | Remaining action |
|---|---|---|
| DRTP is seed-sensitive | Agree. Show all paired seeds, mean/median, worst delta, held-out seed2002 reversal, and use seed sensitivity as a limitation. | Keep raw table in main/supplement. |
| Held-out FAIL invalidates the method | It invalidates a stable-superiority claim, not the descriptive claim of higher average/median historical robustness. | Tone and title must remain bounded. |
| Gains may be absolute-scale or denominator artifacts | Report absolute returns before deltas; do not use self-reference ratios as hard gates; preserve worst seed. | Complete metric audit. |
| This is just more training exposure | UTR/DRTP share the seven topology groups and nominal anchor; identify this as an empirical adaptive weighting question. | Add comparator/ablation only under a new contract. |
| No strong external comparator | Acknowledge MAPPO/UTR are internal controls and old recovery tables are incomparable. | One directly relevant comparator is the main open Q2 gap. |
| Novelty is only reweighting | Position the contribution as a problem–method–reliability package, not a new robust-RL theorem. | Refresh related work and avoid “first” language. |
| Failure exposure is invalid | Report overall unconditional metrics plus survival-to-onset and trigger validity on the risk set. | Include evaluator audit in supplement. |
| Why not claim information loss? | Existing exposed episodes have legal Scout→Attacker direct paths; evidence supports path reorganization, not blackout. | Do not regress wording. |
| Why not use old paper results? | Old EA-RG recovery and Gate1 tables use different estimands/contracts and are marked non-comparable. | Keep them archived only. |

## Reviewer-safe sentence

“The evidence supports a high-average, seed-sensitive topology-robustness effect; it does not support a claim of uniformly reliable superiority.”
