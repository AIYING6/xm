# DRTP Warm-Restart Runtime Persistence Report

## Scope and disposition

**PASS — technical implementation complete; 3M→5M long training remains NOT
AUTHORIZED by this report.**

This report implements and verifies the frozen
`DRTP_WARM_RESTART_MATURITY_EXTENSION_AMENDMENT.md`.  It does not change the
matched Single-Graph architecture (116,728 parameters), DRTP/UTR weighting
equations, PPO, S2 environment, reward, failure semantics, actor information
boundary, seeds, or retention thresholds.  No 420k/430k evaluation tape,
development long run, held-out run, or canonical seed was generated or used.

## 1. Provenance boundary

The verified 3M archive remains SHA256
`2025d3d1b49718e727eb97c87982501eb15b1a7d3c94a33a586082f6da4be1c1`.
Its legacy `actor_critic_training_state_latest.pt` files contain model state,
optimizer state, and update only.  They do **not** contain the mutable
environment, observation, runtime RNG, per-environment episode, or active
DRTP-window states necessary for an exact trajectory continuation.

Accordingly, the amendment correctly classifies the next boundary as a
**checkpoint warm restart**, never a strict resume.  It restores only the
audited legacy subset and reconstructs all four environments symmetrically
with frozen restart RNG seeds.  The 2.5M→3M interval is excluded from the new
maturity clock.

## 2. Runtime-state implementation

Post-warm-restart checkpoints now use
`ri_gmappo_runtime_state_v1` and save every state that can affect the next
rollout/update:

- actor/critic parameters, PPO optimizer, global update and best-evaluation
  bookkeeping;
- Python, NumPy, PyTorch CPU, and CUDA RNG states;
- every 3DOF environment's complete mutable attributes plus both environment
  bit-generator states;
- current `obs`, `share_obs`, graph observation, per-environment episode
  counts and active DRTP episode returns;
- active reset selections and the complete sampler state: `q`, EMA,
  difficulty, adaptation count, and unaggregated returns in every active
  adaptation window;
- explicit `normalization_state: null`, because no normalization state exists
  in this implementation.

`DRTPTopologySampler.state_dict/load_state_dict` validates sampler mode, seed,
simplex mass/bounds, and finite window returns.  The added
`drtp_sampler_total_updates` is a provenance-only protocol horizon field for a
continued invocation; it does not enter policy tensors, rewards, PPO, reset
condition selection, or the DRTP update equation.

Runtime restoration is mutually exclusive with legacy `resume` and
`init_checkpoint`, requires append-only logs, restores environment/sampler
state before the next rollout, and restores global RNG only after constructors
have completed.  This prevents construction-time random draws from changing
the continued trajectory.

## 3. Deterministic continuation test

Technical output:
`results/development/drtp_runtime_state_continuation_test_v3/DRTP_RUNTIME_STATE_CONTINUATION_TEST.json`.

For both arms, a two-update uninterrupted CPU trajectory was compared with an
identical one-update trajectory saved to runtime state, reloaded into freshly
constructed environments, then advanced one update:

| arm | technical seed | result |
|---|---:|---|
| UTR-SG | 99101 | PASS: exact model, optimizer, environment, RNG, sampler, and logs |
| DRTP-SG | 99102 | PASS: exact model, optimizer, environment, RNG, sampler, and logs |

The test uses the frozen 3DOF Single-Graph configuration and 4 environments ×
64 rollout steps, but only two technical updates per comparison.  It is not a
development or performance experiment.  A separate sampler-only round trip
also verifies non-uniform `q`, EMA, difficulty, adaptation count, and a
non-empty active return window before and after the next bounded update.

## 4. Regression checks

All checks below passed after the persistence change:

| check | result |
|---|---|
| Python syntax compilation of modified runtime components | PASS |
| information-boundary regression | PASS (3 tests) |
| S2 graph legality | PASS |
| S2 logging invariance | PASS; maximum numeric difference `0.0` |
| canonical seeds 0–4 used | NO |
| long 3M→5M training started | NO |

## 5. Authorization boundary

The amendment and persistence implementation are now technically sufficient
for one explicitly labelled 3M checkpoint warm restart.  From the first saved
post-restart runtime checkpoint onward, later 5M→6M→…→10M extensions can be
strict continuous resumes with no second warm-restart boundary.

This report neither evaluates plateau maturity nor authorizes the 3M→5M
launch.  A separate decision is still required before any long training,
evaluation tape generation, held-out confirmation, canonical experiment, new
algorithm, loss, encoder, or environment modification.
