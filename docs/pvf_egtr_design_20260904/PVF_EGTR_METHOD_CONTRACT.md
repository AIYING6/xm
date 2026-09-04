# PVF-EGTR method contract

## Purpose

PVF-EGTR is a reliability-oriented training-and-deployment protocol. It preserves the frozen EGTR mechanism as a candidate source of robust-return upside and makes paired UTR the mandatory fallback.

## Frozen method components

1. `UTR`: existing uniform topology sampling and existing SG-MAPPO learner.
2. `EGTR`: the already frozen implementation with confidence kappa `0.20`, required samples `8`, MAD scale `1.4826`, simplex bounds `[0.05, 0.35]`, and post-projection L1 step at most `0.10`.
3. Both arms use the same actor, critic, PPO objective, optimizer, reward, environment, observation, training horizon, and matched seed.
4. Original DRTP is removed from future performance stages; it has already served its mechanistic comparison role.

## Selector contract

- Development selector tape A: episode IDs `730000–730099`.
- Development selector tape B: episode IDs `731000–731099`.
- Selector tapes are generated and hashed before any candidate evaluation.
- They are unavailable to training and disjoint from the completed `720000–720099` tape, all formal/independent/held-out tapes, and future outcome tapes.
- The exact predicate is defined in `PVF_EGTR_MATHEMATICAL_SPEC.md` and implemented only after separate authorization.
- Any missing record, hash mismatch, cross-tape disagreement, practical-effect failure, confidence-bound failure, nominal/worst-group harm, safety failure, or constraint failure selects UTR.

## Prohibited actions

- No EGTR-v2, kappa/L1/simplex retuning, seed replacement, checkpoint selection by final outcome, online telemetry gate, policy mixing, or ensemble averaging.
- No use of formal, independent, held-out, or final outcome tapes in the selector.
- No pooled episodes as independent replicates and no pooled cohorts to conceal disagreement.
- No post-hoc threshold revision.

## What counts as success

Success is not “the selector sometimes chooses EGTR.” It requires, on prospectively independent training seeds:

1. deployed PVF-EGTR has positive mean paired perturbed-return gain over UTR;
2. its lower tail is non-negative within the frozen practical margin;
3. it does not increase catastrophic seeds;
4. nominal, collision, timeout, and constraints remain noninferior;
5. the direction repeats in an independent cohort;
6. the final confirmatory cohort remains untouched until the design is frozen.

## Current authorization

`DESIGN_ONLY`. No training, checkpoint evaluation, tape generation, package creation, or automatic continuation is authorized by this contract.

