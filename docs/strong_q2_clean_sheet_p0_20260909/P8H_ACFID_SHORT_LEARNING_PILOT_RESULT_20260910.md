# P8H ACFID short learning pilot

## Frozen decision

`ACFID_SHORT_LEARNING_PILOT_STOP`.

The pilot used 3,072 sampled high-level recovery decisions per method and seed,
three seeds, and no sealed held-out-combination evaluation. Full 1M training is
not authorized.

## Results against the preregistered gates

- Sealed held-out evaluations: 0 (pass).
- Entropy collapse: none (pass).
- ACFID interaction gradient maximum: 0.199–0.244 across seeds (pass).
- ACFID train-support non-inferiority to Additive: 3/3 seeds (pass).
- Seeds with at least 5% regret reduction: Direct 3/3, Additive 3/3, ACFID 1/3
  (stop).

The ACFID final mean regret was equal to, or slightly below, the Additive value
within the frozen 0.05 margin for all three seeds. However, all policies largely
converged to the same decisions on combinations already represented during
training. The failed self-improvement count partly reflects two ACFID
initializations that were already close to their final deterministic decisions;
this observation does not override the frozen stop rule.

## Scientific interpretation

This result does not show that ACFID fails on unseen combinations: those cases
remain sealed. It shows that a qualification gate restricted to training-support
combinations cannot identify the proposed compositional advantage. Relaxing the
threshold after observing the output would not repair that design defect.

## Required redesign before any additional learning

Freeze a three-way combination split:

1. training support: nominal, singles, and the existing six training pairs;
2. compositional development support: a deterministic, preregistered subset of
   the nine remaining pairs, used only for pilot qualification;
3. final sealed confirmation support: the remaining pairs plus all triples and
   quadruples, never used for optimization, normalization, stopping, or model
   selection.

The development-pair subset must be selected by a declared hash rule rather than
by observed difficulty or method performance. A new short pilot may then test
whether the ACFID representation generalizes beyond seen pairs while preserving
an untouched confirmatory set.
