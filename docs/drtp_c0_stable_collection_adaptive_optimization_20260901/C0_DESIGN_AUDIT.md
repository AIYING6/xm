# C0 design audit: stable collection + adaptive optimization

**Protocol:** `DRTP-C0-STABLE-COLLECTION-ADAPTIVE-OPTIMIZATION-V1`

**Scope:** zero training, zero evaluation, zero algorithm implementation

**Mainline A:** unchanged
**Decision:** `C0_FEASIBLE`

## Candidate structure

This is a new C-line direction, not a repair of the adaptive DRTP sampler.
Training collection stays fixed: the existing fixed-stratified sampler retains
the same nominal exposure and uniform conditional probability over the six
failure groups. No online difficulty score may alter reset selection.

Only a future actor objective could change. With graph-level failure group
`g_i`, per-graph PPO term `ell_i`, and a frozen, positive, bounded group
weight `w(g)`, the candidate is

`L_actor^C = mean_i [w(g_i) ell_i]`, with `w(N)=1` and
`mean_{g in failure groups} w(g)=1` under the fixed uniform failure mixture.

The normalization is essential: it prevents a group-priority signal from
silently becoming a global learning-rate increase. The first candidate would
leave critic loss, rewards, model, PPO epochs, clipping coefficient, and all
environment semantics unchanged.

## What this does and does not claim

PPO is a clipped surrogate optimization method, so positive bounded weighting
defines a coherent **alternative** surrogate; it is not an unbiased estimator
of the original UTR objective and does not inherit a monotonic-improvement
guarantee. [Schulman et al., PPO (2017)](https://arxiv.org/abs/1707.06347)
provides the surrogate-method foundation.

Group-DRO motivates asking whether predefined groups deserve different
optimization emphasis, but it is not evidence that group weighting will remove
training-seed instability. In particular, naive group reweighting can fail to
generalize without appropriate safeguards. [Sagawa et al., Group DRO
(2019)](https://arxiv.org/abs/1911.08731) is therefore a cautionary method
reference, not a performance claim for this project.

This candidate does **not** optimize episode CVaR or cross-seed lower-tail risk
directly. It removes adaptive **collection** feedback and places bounded,
training-only adaptation in the actor aggregation path. Whether that improves
the training-seed lower tail remains an empirical question for a later,
separately authorized experiment.

## Core gates

| Gate | Result | Evidence |
| --- | --- | --- |
| PPO objective validity | **PASS** | `simple_ri_gmappo.py` already computes `policy_per_graph` before building `actor_per_graph` and taking its mean. A bounded positive group multiplier can be introduced at that aggregation point. |
| Training-only isolation | **PASS** | `collect_rollout` stores `condition_group` separately and documents that it is excluded from observation and graph tensors, actor/critic calls, and evaluation interfaces. `FixedStratifiedTopologySampler` uses fixed uniform conditional failure probabilities and has no adaptive `q`. |
| Cost and matched collection | **PASS** | The candidate would reweight existing per-graph actor terms: `O(batch size)` arithmetic, no extra training episodes, probes, or policy forwards. Collection remains matched across UTR and the candidate. |

## Non-negotiable constraints for any later contract

1. The sampler remains fixed-stratified; no difficulty statistic may influence
   failure-group selection, `q`, or reset timing.
2. The first candidate weights failure-sample **actor** terms only. Nominal
   weight remains one and the critic remains ordinary PPO.
3. Difficulty must be a lagged, group-aggregated training-only statistic.
   It may not use evaluation tapes, future information, final seed labels, or
   raw episode length as a score.
4. All weights must be positive, bounded, and normalized to conditional
   failure-group mean one. A future preflight must prove these invariants.
5. A future experiment must report per-group exposure, weights, KL, nominal
   performance, every failure-group endpoint, safety, upper-tail retention,
   lower-tail outcome, and dispersion. The C0 result itself makes none of
   those performance claims.

## Stop state

`C0_FEASIBLE` means only that a properly isolated future candidate can be
designed. It does not authorize C1 implementation, same-rollout updates, seed
pilot training, or automatic continuation.
