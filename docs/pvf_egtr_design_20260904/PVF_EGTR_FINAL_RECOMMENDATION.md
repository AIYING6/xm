# Final design recommendation

## Recommended algorithm

Proceed with **Paired-Validation Fallback EGTR (PVF-EGTR)** as the sole primary candidate.

The recommendation keeps the strongest empirical fact from the completed program—EGTR improved Original DRTP in `10/10` fresh mature seeds—while respecting the equally important fact that EGTR did not beat UTR reliably. It therefore changes the deployment decision, not the frozen EGTR training dynamics.

## Why not restart from scratch

A new sampler, loss, residual policy, or graph gate would discard the one stabilization effect that repeated across both cohorts and would reintroduce unvalidated degrees of freedom. PVF-EGTR instead treats UTR as the reliable base and EGTR as a candidate specialist. This is the smallest design that can exploit the observed upside and explicitly contain its downside.

## Why this is not cosmetic packaging

The method incurs real cost and makes a falsifiable decision:

- two policies must be trained;
- two independent selector tapes must agree;
- an untouched outcome tape can reveal false promotion;
- fallback to UTR is part of the algorithm, not selective reporting;
- all seeds and both promotion/fallback decisions remain in the analysis.

## Current verdict

`PVF_EGTR_P0_FEASIBLE_DESIGN_ONLY`

The next permissible action is a separately authorized, zero-training Stage-1 selector evaluation on existing checkpoints. No new policy training should begin until that retrospective discrimination test passes unchanged.

