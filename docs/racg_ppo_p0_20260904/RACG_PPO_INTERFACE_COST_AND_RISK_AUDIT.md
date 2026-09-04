# RACG-PPO interface, cost and risk audit

## Interface feasibility

| Requirement | Status | Existing basis |
| --- | --- | --- |
| fixed topology exposure | available | `SynchronizedTopologyGroupSampler` already fixes 24 streams and never reads return |
| training-only group labels | available | `condition_group` and `condition_split` are batch metadata, not policy inputs |
| two split group-gradient matrices | small implementation | TGTR already computes batched per-group VJPs on one split; repeat for the second split |
| seven-dimensional robust subproblem | small implementation | only Gram/cosine quantities and seven coefficients are required |
| ordinary fallback | direct | reliability zero uses the ordinary aggregate actor gradient exactly |
| critic isolation | direct | critic loss, optimizer and data remain ordinary PPO |
| evaluation leakage prevention | direct | the candidate has no evaluation-tape argument or final-seed label input |

## Expected cost

RACG-PPO needs two batched group-gradient VJPs per actor epoch plus one ordinary backward pass and a seven-dimensional solve. It removes TGTR's seven candidate forward passes per backtracking chain and the parameter transaction/restore loop. Actual GPU wall time is unknown and must be measured in C1; P0 does not infer cloud cost from CPU timing.

C1 must stop if update wall time exceeds 4x matched Sync-UTR, memory exceeds the available 10 GB class GPU, or numerical regularity requires a high-dimensional covariance matrix.

## Principal scientific risks

1. Adjacent streams share policy and critic errors, so split noises may not be independent enough for the cross-fit identity to be useful.
2. Group-gradient agreement may be low almost everywhere; then RACG-PPO is mathematically safe but scientifically identical to ordinary PPO.
3. Agreement can be locally repeatable yet unrelated to long-horizon seed outcomes, as prior mechanism searches repeatedly showed.
4. Dynamic conflict coefficients can themselves destabilize training. The C1 design must measure coefficient variation and must not add a parameter sweep.
5. Fixed synchronized exposure changes update granularity relative to legacy four-stream UTR. Sync-UTR, not legacy UTR, is the causal mechanism comparator.
6. A soft correction can still harm an individual group. That is intentional: exact empirical non-harm was the mechanism that froze TGTR.

## P0 verdict logic

The candidate is mathematically and mechanically feasible for a same-rollout C1 design because it has an exact ordinary fallback, a strict non-freezing bound, a low-dimensional implementation and a training-only interface. Fresh-seed training remains unauthorized because gradient agreement, actuation and cost have not yet been measured.
