# T1 — Telemetry-Native Fixed-Exposure SG Reference Contract

**Status:** `FROZEN FOR TRAINING-PREFLIGHT ONLY — long training is not yet authorized`  
**Depends on:** `T0-TELEMETRY-NATIVE-V1`  
**Purpose:** establish a clean, reproducible reference trajectory for the
system-robustness paper.  T1 is not a new method screen and cannot revive
DRTP, TCR, SPC, RSG-TC, or any historical superiority claim.

## 1. Reference method

T1 trains exactly one reference: **UTR-SG-MAPPO**.  It is the matched
Single-Graph policy with fixed exposure:

```text
50% nominal episodes
50% failure episodes, conditionally uniform over F0 / TE / TL / DS / DL / CP
```

It must retain the established `116,728` parameter Single-Graph actor/critic,
the existing PPO settings, and the fixed stratified sampler.  Its actor
gradient mode is `utr`, i.e. the normal update with the same paired bookkeeping
path but no projection.  There is no return-adaptive sampling, q/EMA/difficulty
state, curriculum, extra loss, new encoder, reward change, or environment
change.

## 2. Immutable task and information contract

The S2 3DOF task remains unchanged: straight target, strict target sensing,
actor target-information bottleneck, business-grounded geometry, 260-step
horizon, and Relay 1 node-failure semantics.  The actor may receive only the
existing decentralized `obs`, `share_obs`, and graph tensors.  Raw telemetry
must preserve actor-legal inputs and diagnostic-only simulator state in the
separate schema introduced by T0; diagnostics must never be passed to the
policy.

## 3. Prospective development population

Before a training launch, the preflight must verify that the following five
seeds are absent from prior training, tuning, and decision evidence:

```text
2201, 2202, 2203, 2204, 2205
```

They are new **development** seeds only.  Canonical seeds `0–4`, all prior
held-out seeds, and all historical development checkpoints are forbidden.

## 4. Training contract, once separately authorized

Each of the five runs must be from scratch and strictly continuous for
`1,000,192` environment steps (`4 envs × 64 rollout steps × 3907 updates`).
Runtime-state persistence is enabled from update zero.  A run must persist
model, optimizer, global update, Python/NumPy/PyTorch/CUDA RNG, per-environment
runtime state and observations, episode counters, sampler state, and any
normalization state.  Before a production launch, a save → reload → next-update
exact-continuation test is mandatory.

The final 1M checkpoint is the only checkpoint permitted for T1 performance
analysis.  Intermediate checkpoints may be retained solely for learning curves;
they cannot be promoted, selected, or compared as final algorithm evidence.
There is no early stopping, seed exclusion, restart, or extension in T1.

T1 is an evidence-line bootstrap, not a maturity declaration.  At the end of
T1, a separate decision is required before any extension, comparator, held-out,
or canonical experiment.

## 5. Evaluation tape and source of truth

The T1 evaluation tape is not created until long-training authorization, but
its namespace is reserved now:

```text
920000–920099
```

It will contain the same deterministic base IDs across nominal, F0, timing,
duration, and compound perturbation conditions.  Its exact condition list,
manifest, and SHA256 must be written before checkpoints are evaluated.  The
tape is development-only and may never be reclassified as held-out or
canonical evidence.

For every `seed × condition × episode`, the sole source is:

```text
raw_step_telemetry.jsonl
        -> episode_aggregates.jsonl
        -> per-seed condition summary
        -> descriptive table
```

All reductions use float64 from the raw telemetry.  Historical CSVs,
historical float32 summaries, and manually assembled aggregates are forbidden
as inputs to a T1 table or gate.

## 6. Mandatory outcome and safety accounting

Every episode remains in unconditional performance and safety accounting.
Final raw-derived reports must include:

- `J_nominal`, `J_F0`, `J_OOD_mean`, `J_OOD_worst`;
- collision, timeout, constraint violation, terminal step, and episode length;
- pre-trigger collision count/rate, survival-to-onset fraction, risk-set size,
  and trigger success among onset-surviving episodes;
- direct/relay path fraction, path-switch count, task-support fraction, legal
  information fraction, cache age, travelled distance, and control effort.

An episode terminating before failure onset is retained as an unconditional
policy/safety result.  It is not an evaluator defect.  Evaluator validity is
instead checked in the alive-at-onset risk set.

## 7. T1 preflight gates

Before any long training can start, all of the following must pass:

1. T0 source-closure, deterministic replay, logger-noninterference, schema,
   manifest, and append-protection gates remain green;
2. the trained Single-Graph checkpoint adapter uses only actor-legal inputs;
3. raw-checkpoint evaluation is deterministic for the same checkpoint, seed,
   scenario, and episode ID;
4. logged and independently evaluated aggregates agree exactly after canonical
   float64 reduction;
5. the reserved seeds and tape namespace pass provenance checks;
6. a one-update training smoke has the frozen parameter count, fixed sampler,
   runtime-state checkpoint, and no DRTP/TCR/SPC state;
7. all output roots refuse overwrite.

## 8. Stop boundary

This document does not authorize training, tape creation, held-out evaluation,
canonical evaluation, a new method, or a paper claim.  A subsequent explicit
authorization must name the intended T1 run count and allow the reserved tape
to be created.
