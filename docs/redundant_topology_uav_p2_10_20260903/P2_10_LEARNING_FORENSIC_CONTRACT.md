# P2.10 — assigned-baseline learning forensic contract

## Purpose

P2.9 retained all ten 1M trajectories but did not meet the baseline
learnability gate. P2.10 is a **read-only forensic audit**. It asks whether
the corrected learner's optimization telemetry is technically healthy and
whether the terminal actor's raw logits respond at all to the appended,
terminal-local lane-assignment cue.

## Frozen inputs

- P2.9 training runs only: Plain / UTR × seeds 66011–66015;
- existing `train_log.csv` files and checkpoints at `0`, `500k`, and `1m`;
- the enabled assignment-observation interface already used for P2.9.

## Permitted computations

- parse retained PPO scalar logs;
- load retained checkpoints;
- execute actor forward passes on an in-memory reset observation;
- counterfactually swap only the two terminal preference one-hots in that
  in-memory actor input and compare unmasked terminal logits.

The probe takes no environment step, performs no rollout, no PPO update, no
policy evaluation, no checkpoint selection, and reads no development,
independent, or held-out evaluation tape.

## Required outputs

- `P2_10_TRAINING_TELEMETRY.csv`;
- `P2_10_ASSIGNMENT_LOGIT_PROBE.csv`;
- `P2_10_FORENSIC_REPORT.md`;
- `P2_10_FINAL_VERDICT.md`.

## Interpretation boundary

The probe records sensitivity of raw actor logits, not task performance. Any
output is diagnostic evidence only. P2.10 never authorizes a reward change,
environment change, new learner, training, or P3 automatically.
