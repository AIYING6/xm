# DRTP-SEED-S1 RNG Decomposition Audit

Status: `TECHNICAL PREPARATION PASS — S1-A TRAINING NOT YET STARTED`

## Scope

This optional study is isolated from the paper evidence baseline. The historical DRTP results, the `DRTP_Q2_LIMITATION_ONLY` conclusion, and the current manuscript are not rewritten by S1.

## Historical implementation finding

Before this audit, the legacy training path used process-global Python/NumPy/PyTorch RNG state for several purposes. The DRTP topology sampler had a deterministic seed-derived local draw, but action sampling and PPO minibatch ordering were not independently separated from the remaining Torch/NumPy state. Therefore a post-hoc correlation cannot identify an intervention-supported cause.

## S1 opt-in implementation

`algorithms/ri_gmappo/rng_streams.py` defines six independently derived streams:

| Stream | S1 role |
|---|---|
| `init` | actor/critic initialization seed |
| `env` | environment seeds and training-side environment configuration draws |
| `action` | stochastic policy action sampling |
| `minibatch` | PPO minibatch permutation/order |
| `topology` | DRTP condition/group selection seed |
| `eval` | diagnostic evaluation provenance |

S1 opt-in runs use `RIGMAPPOConfig.rng_decomposition=True` and record `rng_stream_manifest.json`. The legacy path remains unchanged when the flag is false. The one-factor regression changes only the topology seed and verifies that the init, environment, action, minibatch, and evaluation probes are unchanged.

## Compatibility smoke

One update was executed for UTR and DRTP with the same 3D SG/PPO configuration and the opt-in streams. Both completed with finite outputs and normal checkpoint/log creation. This is a technical smoke, not performance evidence and not a training-result claim.

## Remaining S1 gate

The independent streams must be used for the frozen S1-A intervention matrix, and every run must carry a complete RNG tuple, config hash, checkpoint hash, device, tape namespace, and telemetry schema. No S1-A result is interpretable until the pre-registered gates and diagnostic tape manifest are present.

