# R1 zero-training forensic report

Archive SHA256: `a54406e8d2d14c4bc9fa25ea43388595c19f41d476631e1c743512c6c30c0b10`. No checkpoint was rolled out and no training was started.

## Frozen R1 outcome

Gate: `R1_NO_GO`. Failure-group Conservative seeds are 3001, 3003, 3004; success-group seeds are 3002, 3005.

## Safety implementation reconciliation

Existing R1 gate reported aggregate safety `True`. Independent per-seed/condition recalculation found max timeout delta `0.1700`, max collision delta `0.0500`, and `5` records exceeding a 0.10 per-cell delta threshold. Thus the R1 gate used aggregate safety only; this is a gate-implementation mismatch with the earlier S1/S2 per-cell rule. It cannot reverse R1_NO_GO because all non-safety core criteria already failed.

## Provenance

All 15 manifests report execution commit `434b8720`, which is a descendant of readiness commit `591f6ff2`; the cloud package delivery commit `305e5833` only adds git-less provenance fallback. Algorithm/sampler semantics are not changed by that fallback.

## Available evidence and limitation

The archive contains all four milestone checkpoints but only final-1M evaluation records. Therefore milestone reward/PPO/sampler dynamics are extracted here; milestone J_pert_mean, nominal and condition-specific task scores would require a separately authorized zero-training cloud evaluation of the frozen checkpoints. No causal mechanism is claimed from these associations.
