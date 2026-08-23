# DRTP S1-R Protocol v2 — Frozen Numerical Contract

## 1. Scope and historical preservation

This is a prospective protocol freeze for the DRTP seed-reliability causal
screen. It is not a training authorization. The prior v1 execution result
`F_PROTOCOL_UNDERSPECIFIED` remains historical and is not changed.

The contract permits the two existing methods `utr_sg` and `drtp_sg` only. It
does not change either method, the SG backbone, PPO, reward, environment,
failure semantics, actor information boundary, or DRTP implementation.

## 2. Existing evidence and deterministic G/B selection

Only `artifacts/drtp_reliability_a0/rel_a0_decision.json` is used. For seed
`s`, failure family `m` in `{F0, TIMING, DURATION, COMPOUND}`, and tape `t`:

\[
D_{s,m,t}=J_{DRTP}(s,m,t)-J_{UTR}(s,m,t).
\]

For timeout, the tape-level value is the arithmetic mean of the four failure
condition timeout rates, and:

\[
D_{s,TIMEOUT,t}=timeout_{UTR}(s,t)-timeout_{DRTP}(s,t).
\]

G eligibility requires both conditions:

1. `mean_t(D[s,m,t]) > 0` for all four return families;
2. at least three of the four return families have `D[s,m,t] > 0` on at least
   four of five tapes.

B eligibility replaces `>` with `<` in both conditions.

G tie-break, in descending lexicographic order:

1. number of return families favorable on all five tapes;
2. `min_m median_t(D[s,m,t])`;
3. `mean_m median_t(D[s,m,t])`;
4. `median_t(D[s,TIMEOUT,t])`;
5. smallest numerical seed.

B tie-break, in descending lexicographic order:

1. number of return families unfavorable on all five tapes;
2. `max_m median_t(D[s,m,t])` with the smallest value preferred;
3. `mean_m median_t(D[s,m,t])` with the smallest value preferred;
4. `median_t(D[s,TIMEOUT,t])` with the smallest value preferred;
5. smallest numerical seed.

The machine-generated result selects G=`2001` and B=`2002`. The complete
candidate table and per-tape differences are in `gb_selection.json`.

## 3. Scientific runs, references, and budget

The reference phase consists of two from-scratch 1,000,192-step runs:

- `G_REF`: UTR and DRTP reference candidates are trained using the selected G
  and B seed identities as defined by the reference contract;
- `B_REF`: the same two method configurations are used for the B seed.

For the intervention phase, the two selected source identities are each run
under five one-stream substitutions. The total is 12 scientific runs: two
reference runs per method/identity contract plus ten one-stream intervention
runs. No selective rerun or extension is allowed.

Fixed values:

- env steps per scientific run: `1,000,192`;
- total scientific runs: `12`;
- maximum scientific env steps: `12,002,304`;
- technical smoke maximum: `20,000` env steps, excluded from scientific totals;
- milestones: `250,048`, `500,096`, `750,144`, `1,000,192`;
- milestone checkpoints are diagnostic only and cannot be promoted;
- no early stopping, budget extension, seed exclusion, or intermediate-checkpoint
  result substitution.

## 4. RNG decomposition and intervention tuples

The only permitted splitter is
`algorithms/ri_gmappo/rng_streams.py`, using
`RNGStreams.from_master(master_seed)`. The six streams are:

`init`, `env`, `action`, `minibatch`, `topology`, `eval`.

The derivation is:

`blake2b(base_seed, stream_name, components) -> signed-31-bit seed`.

The actual G and B six-integer tuples, source hash, and regression artifact hash
are frozen in `rng_tuples.json`.

For each intervention, exactly one named stream from B is replaced by the
corresponding G stream. The remaining five B streams are retained. The
evaluation stream is fixed and is not replaced by an intervention.

## 5. Evaluation contract

The evaluation contract imports REL-A0 tapes T0–T4 and their hashes from
`eval_manifest.json`. Their episode namespaces are 440000–440099,
450000–450099, 460000–460099, 470000–470099, and 480000–480099. The five
conditions are nominal, F0, timing, duration, and compound. No tape is
regenerated.

TP50 contains the first 10 episode IDs from each imported tape. It is a
telemetry/probe subset only; it cannot replace the full evaluation tapes.

The failure risk set is the episodes alive immediately before scheduled failure
onset. Pre-onset terminations remain in all overall return and safety metrics
and are reported separately. No episode is deleted or relabeled as exposed.

## 6. Reference gate

For each return family `m`, define quality `Q_m = J_m`; for timeout define
`Q_TIMEOUT = -timeout`. Let:

`Gap_m = Q_G_REF,m - Q_B_REF,m`.

The reference gate passes only when all conditions hold:

- R1: `mean_t(Gap_m) > 0` for all four return families;
- R2: at least three of four return families have `G_REF > B_REF` on at least
  four of five tapes;
- R3: mean timeout quality for G is greater than B and G has better timeout
  quality on at least three of five tapes.

If any condition fails, the result is `F_REFERENCE_NOT_REPRODUCED` and all
interventions stop before scientific intervention runs.

## 7. Rescue and reverse-degradation criteria

For every return family and timeout, use quality values and define:

\[
C_{rescue,m}=\frac{Q_{B\to G,m}-Q_{B\_REF,m}}
{Q_{G\_REF,m}-Q_{B\_REF,m}},
\qquad
C_{degrade,m}=\frac{Q_{G\_REF,m}-Q_{G\to B,m}}
{Q_{G\_REF,m}-Q_{B\_REF,m}}.
\]

For each coefficient family, all of the following are fixed:

- per-metric coefficient threshold: `>= 0.35`;
- favorable tape count: `>= 4/5`;
- overall dimensions: `F0`, `TIMING`, `DURATION`, `COMPOUND`, `TIMEOUT`;
- passing overall dimensions: `>= 4/5`;
- passing return dimensions: `>= 3/4`;
- median coefficient threshold: `>= 0.40`;
- minimum allowed coefficient: `-0.20`; any coefficient at or below it fails.

The rescue and reverse-degradation sections use the same thresholds. A
one-stream intervention cannot be called causal from one direction alone.

## 8. Precursor consistency

Only milestone `500,096` is confirmatory. Milestones `250,048`, `750,144`, and
`1,000,192` are exploratory. The precursor window is steps `0..39` relative
to failure onset, applied only to TP50 episodes in the risk set.

Fixed precursor metrics:

- P1: `(task_progress[39] - task_progress[0]) / 40`; higher is better;
- P2: `count(stagnation == 1) / 40`; quality is the negative fraction;
- P3: `1` if `task_stage[39] > task_stage[0]`, otherwise `0`.

Reference separation requires a positive reference gap, G better than B in at
least three of four failure families, and at least two of three precursor
metrics eligible. Otherwise the label is
`F_PRECURSOR_REFERENCE_NOT_SEPARATED`.

For rescue and reverse directions, a precursor coefficient must be at least
`0.30`, have the expected direction in at least three of four failure families,
use the same milestone and window, and at least two of three precursor metrics
must pass.

## 9. Required telemetry schema

Every confirmatory TP50 record must provide these fields:

`episode_id`, `env_step`, `failure_relative_step`, `agent_role`, `position`,
`velocity`, `sampled_action`, `executed_action`, `task_stage`, `task_progress`,
`stagnation`, `graph_state`, `active_edges`, `failure_state`, `terminal_reason`,
`timeout`, `collision`, `constraint_violation`, `actor_loss`, `critic_loss`,
`entropy`, `KL`, `clip_fraction`, `gradient_norm`, `DRTP_group_weights`,
`DRTP_group_signal`, `probe_id`, `probe_policy_output`, `milestone`.

## 10. Outcome labels and hard stop

The only outcome labels are:

`A_ACTIONABLE_SINGLE`, `B_MULTIPLE_ACTIONABLE`, `C_ONE_WAY_ONLY`,
`D_NO_SOURCE`, `E_TRAJECTORY_NO_SOURCE`, `F_REFERENCE_NOT_REPRODUCED`,
`G_TECHNICAL_INVALID`.

Any missing required field, failed deterministic audit, checkpoint corruption,
or continuation mismatch is `G_TECHNICAL_INVALID`. No scientific claim can be
made from a technically invalid run.

This amendment stage stops after static protocol validation. Training,
evaluation, telemetry smoke, checkpoint creation, and intervention execution
are all disabled until separately authorized.
