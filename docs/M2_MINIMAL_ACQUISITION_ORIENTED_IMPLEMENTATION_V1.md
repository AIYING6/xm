# M2 minimal acquisition-oriented implementation v1

**Status:** `M2_IMPLEMENTATION_PASS__READY_FOR_FROZEN_TWO_SEED_PILOT`

## Scope

M2 implements only a paired, explicit-state actor interface.  It does not
launch training and does not modify the L4 task, reward, recipient-specific
actor contract, critic, communication mechanics, physical neutralization
definition, hybrid action semantics, or role-action masks.

| Arm | Legal temporal input | Fusion/control operation |
| --- | --- | --- |
| Full | Same current legal target fields, target-history GRU, target-free self-history GRU and previous executed action as B1. | An unsupervised progress latent multiplicatively modulates target history before fusion. |
| B1 | Exactly the same fields, histories, previous action, hybrid action heads and role-head layout. | Direct additive fusion through an equal-shape projection; no progress-conditioned modulation. |

The two arms deliberately use identical module shapes and therefore have an
exact parameter match.  The only architectural distinction is the use of the
common progress/projection path in the fusion operation.

## Legal-memory contract

The target-history GRU accepts an explicit boolean `evidence_valid`.  Its
caller must derive it exclusively from the already-frozen contract:

`current local sensing OR delivered and cache-valid target evidence`.

When false, target fields are zeroed at the GRU input and its hidden state is
zeroed both before and after the GRU update.  Consequently a pending, dropped,
expired or globally inferred target value cannot alter target state or policy
output.  The self-history path excludes target values, direct-detection,
attack-window and cache-age/confidence fields, so it cannot become a second
target cache.  Episode-boundary reset remains a collector obligation and is
explicit in the public state API.

## M2 gate

Before any pilot, the deterministic M2 suite must show: legal evidence updates
target state; expiry clears it; changing expired payload cannot change the
actor output; Full/B1 parameter counts match; and hybrid action log-probability
continues to score exactly the executed bounded action.  Existing actor
boundary, target-contract, continuous-action and role-head suites remain
required regressions.

## Not yet authorised

No pilot, training, evaluation, reward adjustment, new task mechanism, new
graph/message module, or formal result claim was performed in M2.  The next
separate authorisation may connect this explicit-state policy to a collector
and launch the pre-frozen two-seed, 60-update Full-vs-B1 development test.
