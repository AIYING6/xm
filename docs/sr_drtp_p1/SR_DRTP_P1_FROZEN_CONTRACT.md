# SR-DRTP P1 frozen shadow-utility contract

**Status:** `PREPARATION_ONLY`; `P1_EXECUTION_NOT_AUTHORIZED`.

P1 asks whether a training-time signal predicts that a specified temporary
intervention is better than continuation from the same state. It does not ask
whether a seed will ultimately be good or bad.

## Frozen prospective structure

- Cohort A: 4401--4405; Cohort B: 4406--4410. They are analyzed separately.
- Official trajectory: Original DRTP only, 1,953 updates / 499,968 formal
  training interactions per seed; no formal or held-out evaluation tape.
- Candidate source updates: 256, 512, 768, 1024, 1280, 1536 and 1792.
- At each source, a complete runtime snapshot yields three 16-update branches:
  A Original exact continuation; B temporary 20% uniform sampler anchor; C a
  one-shot next-PPO-update actor rollback with the critic retained. B+C is
  forbidden.
- Branch outcome is mean training reward over the fixed 16-update horizon.
  It is a conditional utility label, not a final-performance claim.

## Signals and gate

The primary rule is two consecutive scheduled PP-versus-online top-risk-group
disagreements. q instability and PPO stress fields are secondary diagnostics;
they cannot replace the primary rule or be used in a fitted classifier. PP
probes use 4 common base IDs × 7 groups, remain training-only, and are excluded
from PPO buffers and official RNG streams.

P1 can pass only if temporal precedence, conditional discrimination, low false
positives, and directionally consistent cohort-A/cohort-B evidence all hold at
the training-seed level. Any pooled event calculation is descriptive only.

## Hard boundaries

No selector, SR-DRTP algorithm, long trajectory, evaluation tape, seed
replacement, performance rerun, threshold sweep, or automatic continuation is
authorized. A P1 pass would authorize only a subsequent design audit, never
automatic algorithm training.
