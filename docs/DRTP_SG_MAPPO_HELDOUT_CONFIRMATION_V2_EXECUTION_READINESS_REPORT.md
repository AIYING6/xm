# DRTP-SG-MAPPO Held-Out Confirmation v2 Execution Readiness Report

## Status

**READY FOR THE SIX EXPLICITLY AUTHORIZED HELD-OUT TRAJECTORIES ONLY.**

The controller maps `DRTP_SG_MAPPO_HELDOUT_CONFIRMATION_CONTRACT_V2.md` into
six from-scratch, strict-continuous 10M trajectories: UTR/DRTP × seeds
2001/2002/2003.  Runtime-state persistence is active from update zero; all
checkpoint labels are curve-only and the 10M final checkpoint is the only
method-comparison checkpoint.

## Frozen execution behavior

- creates exactly the v2 paired held-out tape `430000–430099` at launch;
- trains only 39,063 updates / 10,000,128 steps per run;
- evaluates six 10M final checkpoints across 12 frozen conditions (7,200
  episodes total) with training seed as the inference unit;
- applies unchanged nominal/F0/OOD absolute, seed-consistency, safety, and
  exposure gates;
- reports `R_OOD_mean` and `R_OOD_worst` for every seed and pooled estimate as
  descriptive diagnostics, with `self_reference_is_hard_gate=false` hardcoded
  into the final aggregation artifact.

The controller cannot launch canonical seeds, a formal five-seed study,
ablations, a new algorithm, or follow-on OOD experiments.

## Technical launch checks

`scripts/verify_drtp_sg_heldout_v2_contract.py` checks without training that
the six authorized cells, seed set, 10M budget, 116,728-parameter SG identity,
runtime persistence, no-resume/no-warm-restart rule, frozen sampler/task, and
430k held-out tape contract are all intact.
