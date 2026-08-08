# Primary estimand v1.7

## Target quantity

The primary endpoint is the time from relay-failure onset to the start of the
first stable task-chain window observed after exposure:

\[
T_{est}=s_{win}-s_f, \qquad
s_{win}=s_{end}-K+1.
\]

Here `s_f` is `node_failure_start_step`, `s_end` is the final step of the
episode, and `K` is `attack_hold_steps`. In the locked evaluator, `K=4` by
default. A window is admissible only when it contains `K` consecutive steps
whose `chain_closed` state is true. `chain_closed` is produced by the
environment when `attack_hold >= attack_hold_steps`; `attack_hold` increments
only when an attack window, positive tracking, and a communication path to the
attacker coexist, and otherwise resets to zero.

The evaluator sets `post_failure_chain_recovered=1` when any post-onset
`chain_closed` step exists, and computes the event clock from the stable-window
start (`post_failure_chain_recovered_only_steps`). In v1.7 this field is
renamed conceptually to stable-task-chain establishment; the raw v1.6 column is
not altered.

## Analysis population and censoring

The primary population is the locked failure-exposed Early+Nominal evaluation
set. Each method is evaluated on matched episode identities within a training
seed. Training seeds are independent experimental units; episodes are samples
nested within seed and are not independent replacements for training seeds.

For the P3-A raw protocol, an episode contributes exactly one pair:

- event: `recovery_event_time = recovered_only_steps` when a stable window is
  observed;
- censor: `censor_time = steps - failure_start_step` when no stable window is
  observed.

The censor time therefore represents the actual available post-onset follow-up
until episode termination (success, collision, constraint violation, or
timeout), as recorded by `final.step`; it is not automatically a collision-at-
horizon censor. The fixed horizons used by the locked protocols are `tau=80`
(the pre-specified active relay-failure window) and `tau=220` (full follow-up
restriction). Episodes that terminate before the relevant follow-up contribute
their available censor time.

The estimator is the Kaplan–Meier survival estimate of time to establishment,
with restricted mean

\[
RMST(\tau)=\int_0^\tau \hat S_{est}(t)\,dt.
\]

Smaller RMST means earlier stable-task-chain establishment within `tau`.

## Matched structure and aggregation

The primary contrasts preserve the locked matched episode structure and compare
EA-RG with MAPPO on the same protocol population. Hierarchical paired
bootstrap contrasts resample training seeds as the outer unit and matched
episode pairs within each selected seed as the inner unit, then recompute the
RMST contrast. Seed-level summaries are reported separately from pooled episode
descriptives.

The conditional mean `t_est` (formerly recovered-only `t_rec`) is calculated
only among episodes with an observed establishment event. It is descriptive and
does not replace KM/RMST because conditioning on observed events changes the
estimand and discards censored episodes.

## Scope boundary

This estimand does not require, and the locked data do not establish, a prior
stable chain followed by observed loss and later re-establishment. The separate
`post_failure_chain_recovered_after_loss` field is the diagnostic for that
stronger event and was zero in the formal audit. Claims about true
post-disruption recovery are therefore outside this primary estimand.
