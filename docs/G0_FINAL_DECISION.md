# G0 final decision

## Decision

**C — NO_ACTIONABLE_TOPOLOGY_GENERALIZATION_GAP**

## Evidence boundary

G0 is a zero-shot, frozen-policy, development-only validation. It used the frozen topology manifest and existing checkpoints only. No training, optimizer step, checkpoint promotion, held-out seed, or canonical seed was used.

The exact primary decision was computed from UTR-SG-MAPPO's five T1 clean development seeds using the pre-registered structural-versus-parameter gap rules. Historical DRTP checkpoints remain separate descriptive evidence and do not change the primary decision.

## Interpretation

The decision is not a claim of universal graph generalization. It is a bounded statement about whether the fixed-size legal U1–U5 topology family produces an actionable zero-shot gap relative to the seen Relay-failure family and its timing/duration comparator.

## Required stopping rule

The G0 phase stops here. No DRTP-v2, new encoder, new loss, canonical seed, held-out experiment, or additional training is authorized by this report. Any next phase requires a separately frozen contract.

## Audit assets

- `docs/G0_TRAIN_TOPOLOGY_EXPOSURE_MANIFEST.md`
- `docs/G0_FROZEN_UNSEEN_TOPOLOGY_SUITE.md`
- `docs/G0_TOPOLOGY_LEGALITY_AND_FEASIBILITY_AUDIT.md`
- `docs/G0_ZERO_SHOT_RESULTS.md`
- `docs/G0_STRUCTURAL_VS_PARAMETER_OOD.md`
- `docs/G0_GENERALIZATION_GAP_ANALYSIS.md`
- `docs/G0_PRIOR_ART_AND_REVIEWER_ATTACK.md`
- `artifacts/g0/generalization_summary.json`
