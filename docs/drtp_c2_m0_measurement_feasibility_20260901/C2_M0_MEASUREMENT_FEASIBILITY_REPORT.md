# C2-M0 measurement feasibility report

**Verdict:** `C2_M0_FEASIBLE`.

| Requirement | Result | Existing interface evidence |
| --- | --- | --- |
| Per-group actor/critic gradients | `True` | `group_credit_telemetry.py` computes read-only `torch.autograd.grad` summaries. |
| Per-group advantage and clipped PPO quantities | `True` | Raw/normalized advantage summaries and the clipped PPO objective are available at the read-only diagnostic site. |
| Pairwise gradient conflict | `True` | Actor/critic dot products and cosines are logged. |
| Scout/Relay/Attacker behavior | `True` | Chosen actions, support/path states and failure windows are logged without second action sampling. |
| Fixed training-state checkpoints | `True` | Milestone model/training/runtime checkpoint paths already exist. |
| Default-off and no control feedback | `True` | Writers are optional output sinks; group credit contains no optimizer step. |
| No formal-tape read in training interface | `True` | Training configuration does not accept a tape input. |

## Cost accounting (static, not benchmarked)

At the frozen `32`-update interval, each `1953`-update trajectory has `61` diagnostic updates (3.12% of updates), `427` group summaries, `1281` pair-conflict summaries, and `854` diagnostic actor/critic autograd calls. The interface adds **zero** environment interactions and uses already-collected rollout batches. Wall-clock and disk overhead remain a mandatory future preflight measurement.

## Important output limitation

The current group-credit CSV already emits group advantage summaries and gradient quantities, but it does **not** yet emit the scalar clipped actor-loss contribution itself. M0 establishes that this scalar is available at the same read-only calculation site; a later explicitly authorized measurement-only implementation would need to append it to the telemetry schema. M0 does not make that implementation change.

## Strict interpretation

M0 passes only the feasibility question. It does not repair C2, make C2-D1 causal, authorize a new stabilizer, or permit training. A later diagnostic protocol must include fresh seeds, fixed checkpoint timing and outcome-blind analysis; it must stop if no repeated signal maps to one minimal intervention.
