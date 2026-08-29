# PP-DRTP design audit

## Decision

`D7_DESIGN_AUDIT_PASS — implementation and training remain unauthorized`.

This audit follows D6 decision artifact SHA256
`67030744e9304782a346a488b7abd6e3e2f39f92d0d693668efef35c8f09c177`.
It defines one mechanism-aligned candidate for a later independent technical
audit. It does not alter Mainline A, existing DRTP, the D5 result, or any
checkpoint.

## Candidate: paired-probe DRTP (PP-DRTP)

Original DRTP computes its group EMAs from completed training episodes. Those
episodes were selected using the current sampler distribution `q`; therefore
the measurement stream is exposure-dependent. PP-DRTP keeps the DRTP policy,
PPO, reward, environment, nominal mass, groups, bounded-simplex update and
all actor/critic inputs unchanged. It changes only the data source used for
the sampler's group-return estimate.

At every existing adaptation boundary after the existing warm-up, PP-DRTP
creates a training-only probe micro-batch. For each deterministic base probe
identifier `z`, it executes one nominal rollout and one rollout for each
failure group from the same environment seed and with deterministic policy
actions. These rollouts are never placed in the PPO rollout buffer.

For group `k`, the probe summaries are

\[
\widetilde J_{N,u}=\operatorname{median}_{z\in\mathcal Z_u} J_N(z),
\qquad
\widetilde J_{k,u}=\operatorname{median}_{z\in\mathcal Z_u} J_k(z),
\]

followed by the **unchanged** DRTP update

\[
d_{k,u}=\operatorname{clip}\!\left(
\frac{\bar J_{N,u}-\bar J_{k,u}}
{\max(|\bar J_{N,u}|,10^{-8})},0,2\right),
\]

where the EMA uses the pre-existing `kappa=0.20`. The pre-existing
exponentiated update, `eta=1.0`, `beta=0.50`, `q_k in [0.05, 0.35]`, and
nominal exposure `0.50` remain unchanged.

The paired differences `J_N(z)-J_k(z)` are telemetry and a variance audit;
they do not define a new reward, loss, or actor/critic feature.

## Why this differs from failed candidates

TR and uniform anchoring restricted the sampler output. KLR/KLB altered actor
updates. PP-DRTP changes neither: it preserves DRTP's ability to concentrate
training on difficult groups, but makes the evidence used to choose those
groups balanced and independent of the current training exposure allocation.

This directly targets the D6 pattern

\[
\text{small actor perturbation} \rightarrow \text{return change}
\rightarrow q\text{ divergence} \rightarrow \text{exposure feedback}.
\]

It does not claim that this pattern is the cause of Original DRTP's broader
seed sensitivity.

## Frozen implementation requirements for a future P2 audit

The P2 audit must select the single probe-batch size and identifier namespace
before any PP-DRTP result is inspected. The default design candidate is four
base identifiers per adaptation boundary, chosen because the frozen trainer
uses four parallel environments; this is a coverage rule, not a performance
sweep. Any other size requires a new design audit, not a cloud rerun.

Required technical properties:

1. Probe environments are newly constructed from deterministic, training-only
   seeds and do not reuse a confirmatory evaluation tape.
2. The same base seed is used for the nominal and every failure-group rollout
   within a probe identifier; failure configuration is set before reset.
3. Probe actions are deterministic; the probe code uses `torch.no_grad()` and
   temporarily sets the agent to evaluation mode, then restores its mode.
4. Probe rollouts do not consume training-environment RNG, PPO minibatch RNG,
   sampler-selection RNG, optimizer state, normalization state, or rollout
   buffer capacity.
5. Probe return summaries, base identifiers, condition, duration, EMA input,
   paired gap and final `q` are persisted in sampler runtime state and logged.
6. Save/reload in the middle of a probe boundary reproduces the same probe
   records and next sampler update exactly.
7. UTR and Original DRTP code paths remain byte-for-byte behaviorally
   unchanged when PP-DRTP is disabled.

## Required P2 decision before any pilot

P2 may authorize a clean-seed PP-DRTP pilot only if tests demonstrate
trajectory/RNG invariance with PP-DRTP disabled, probe isolation, paired-reset
equivalence, simplex preservation, exact save/reload, and no probe transition
in the PPO buffer. It must also report the measured probe-rollout overhead.

No seed, evaluation tape, pilot budget, success margin, or cloud launch is
authorized by this document.
