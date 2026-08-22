# DRTP-SEED-S1 Pre-Registered Gates

Status: `FROZEN BEFORE S1-A MAIN RUNS`

## Primary outcomes

Each intervention is compared with its matched good/weak reference pair using `J_F0`, `J_OOD_mean`, `J_OOD_worst`, and failure timeout. The unit is a complete training trajectory, not an episode.

For each metric, define the reference gap as the good-reference value minus the weak-reference value, with timeout sign reversed so that larger means better. Define gap closure as the intervention change divided by the absolute reference gap plus `1e-8`.

## Candidate-factor gate

An RNG source is a candidate only if all conditions hold:

1. the factor-only intervention changes the matched good-minus-weak gap by at least `0.50` standardized reference-gap units on at least two of the four primary outcomes;
2. the direction improves the weak-side outcome without reducing nominal competence by more than `0.20` standardized nominal units;
3. the change is present by or before the frozen divergence window identified from the milestone curves;
4. the effect exceeds the reference pair's within-trajectory temporal fluctuation, defined as the 75th percentile absolute milestone-to-milestone change;
5. the factor does not pass only through timeout while all return metrics worsen.

These are diagnostic gates, not superiority thresholds.

## Confirmation gate

An actionable factor requires both directional transfer and rescue transfer, at least three independent paired confirmation tuples, and temporal precedence. One good-looking seed or one rescue of seed2002 is insufficient.

## Branching gate

Checkpoint branching may be interpreted as basin commitment only if the same checkpoint produces at least two strong and two weak continuation classes across independent future RNG continuations, the class split is reproduced at two checkpoints or two source trajectories, and no single RNG factor passes the candidate-factor gate.

## Coordination precursor gate

A precursor must be actor-legal/physical, appear before final failure, recur in at least two weak branches, be materially weaker in strong branches, and survive a counterexample search. A metric that is merely a transformed final return is not a precursor.

## Stop rules

`E — NO_ACTIONABLE_CAUSAL_LEVER` is mandatory if no intervention survives replication and counterexample checks. `F — TECHNICAL_INVALID` is reserved for broken stream independence, invalid continuation, contaminated tape, or changed training semantics. No algorithm design or stabilized training is authorized by these gates.

