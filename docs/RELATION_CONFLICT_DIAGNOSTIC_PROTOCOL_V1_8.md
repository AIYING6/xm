# RELATION_CONFLICT_DIAGNOSTIC_PROTOCOL_V1_8

**Status: preregistered/frozen before formal results.** This suite is
diagnostic, not a replacement for nominal primary evaluation.

## Common information contract

Every method receives the same recipient-specific raw packet/cache view and the
same environment seed, action-policy evaluation seed, episode count, and
failure timing. No EA-RG-only flag, relation label, critic field, or simulator
global is added. The scenarios differ only through fixed environment state,
sensing, communication delivery, age, and task geometry.

## Fixed conflict scenarios

1. **Sensing available / communication unavailable:** local target sensing is
   valid while the relevant teammate packet is dropped or outside the legal
   communication window.
2. **Communication available / sensing unavailable:** a delivered teammate
   packet is valid while local target sensing is unavailable.
3. **Delivered but stale communication:** the last delivered packet remains
   cache-valid with increasing age and fixed confidence decay.
4. **Communication available / task-support inactive:** a delivered packet and
   communication edge exist, but role/task geometry does not satisfy the frozen
   task-support predicate.
5. **Relay-failure disagreement:** failure removes delivery while stale legal
   cache state and local sensing evolve under the fixed failure onset.

Each scenario has a fixed seed list and fixed action sequence generated before
any method is evaluated. All episodes are reported, including zero-conflict
episodes.

## Metrics

Per time step and receiver, report relation edge counts, active rates, pairwise
overlap/Jaccard, complete-mask equality, disagreement rate, delivered
communication edges without task-support, task-support/communication ratio,
packet age/confidence, and downstream encoder attention entropy. Report the
scenario-level distribution and seed-level summaries. Do not rank scenarios by
EA-RG effect size or select a subset after observing results.

## Interpretation lock

The suite can establish whether relation channels encounter distinct legal
states. It cannot by itself establish performance superiority. Any structural
change prompted by a conflict result requires a new protocol version and a new
author decision.
