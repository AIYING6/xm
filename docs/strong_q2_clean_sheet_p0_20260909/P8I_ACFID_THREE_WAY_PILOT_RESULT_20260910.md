# P8I ACFID three-way compositional pilot

## Decision

`ACFID_COMPOSITIONAL_DEVELOPMENT_GATE_STOP`.

Do not run the 1M-per-method pilot and do not evaluate the sealed confirmation
set.

## Evidence isolation

The split was frozen before execution. Four of the nine unseen pairs were
selected mechanically by ascending SHA256 under salt `P8I-20260910`; five
remaining pairs, all triples, and all quadruples stayed sealed. The run made
zero evaluations on the sealed support.

## Gate results

- ACFID improves Additive development-pair regret by at least 5%: 0/3 seeds
  (stop).
- ACFID is non-inferior to Direct within absolute regret 0.03: 2/3 seeds
  (pass).
- Removing the learned interaction term worsens development regret by at least
  3%: 0/3 seeds (stop).
- Training-support guard against Additive: 2/3 seeds (pass).
- Entropy collapse: none (pass).

Development regrets were identical between ACFID and Additive for all three
seeds (0.3240, 0.2902, and 0.3191). The no-interaction ACFID view also produced
the same decisions in two seeds and a slightly lower regret in the third. Thus,
the proposed interaction representation received gradients but did not exert a
reliably beneficial decision-level effect.

## Interpretation boundary

The result does not establish that compound-fault interaction modelling is
generally useless. It rejects this specific combination of synthetic task,
observable signatures, action set, ACFID representation, and short-PPO
learning formulation as a qualified route to the claimed compositional gain.
Continuing to the large budget would test persistence, not repair causal
identifiability.

## Recommendation

Stop the current ACFID candidate. Before designing another method, run a
zero-training audit on a defensible UAV task implementation or archived valid
trajectories to answer one question: do compound events change the optimal team
decision beyond what single-event effects predict? The audit must quantify the
decision-flip rate, additive-policy regret, recoverability range, and available
causal observations. If that real-task gap is absent, abandon this topic rather
than manufacture it through environment coefficients.
