# A0 novelty red team: information-compatible CTDE

Status: preliminary red-team conclusion; no mechanism implementation authorized.

## What is already established in the literature

- Lyu et al. formally analyze centralized, state, and history critics under
  partial observability, including the possibility that state-based critics
  induce bias and variance, and explicitly discuss history-state critics as a
  way to combine history and state information.  [Paper](https://arxiv.org/abs/2408.14597)
- Lambrechts et al. provide a finite-time justification for asymmetric
  actor-critic algorithms with additional training-only state information.
  [ICML 2025 paper](https://proceedings.mlr.press/v267/lambrechts25a.html)
- Xiao, Lyu and Amato's ROLA already combines a local action-value/advantage
  critic with centralized training to improve multi-agent policy gradients.
  [Paper](https://arxiv.org/abs/2110.08642)

These works make it untenable to claim novelty merely from: “a centralized
critic has privileged information”, “use a local critic”, “condition an
advantage on local history”, or “distil a central critic into a local one.”

## A0 equivalence test

For an existing policy and trajectory distribution, the candidate

`E[A_central | I_i^legal, a_i]`

is precisely an information-conditional regression target.  Without an
additional objective, estimator theorem, or constraint, learning it with a
local/history network is operationally a local history/action-value critic.
Subtracting the residual is likewise a standard conditional-expectation
projection/control-variate operation.  Consequently, the currently specified
candidate is not yet distinguishable from existing history/local critic and
advantage-estimation lines.

## Required distinction if this line is ever reconsidered

Any future candidate would need all of the following *before* code is written:

1. a policy-gradient objective whose estimator is not equivalent to replacing
   the centralized critic by a local/history critic;
2. a stated bias/variance or optimization property under the recipient-specific
   information sigma-algebra;
3. a comparator set containing capacity-matched local-history, history-state,
   ROLA-style, and critic-distillation baselines; and
4. a proof or exact derivation explaining what the privileged residual may do
   during critic learning but cannot do in the actor update.

Absent that distinction, the appropriate A0 novelty result is a no-go even if
the read-only mismatch audit observes a large centralized-value sensitivity.

## A0 novelty verdict

`A0_NO_GO__CURRENT_LEGAL_ADVANTAGE_PROJECTION_REDUCES_TO_EXISTING_HISTORY_LOCAL_CRITIC_LINE`

This verdict concerns the current proposal only.  It does not dispute the
scientific relevance of critic-information mismatch, and it does not license a
renamed local critic as a new main method.
