# Scientific upgrade Phase 2I-A final architecture report

**Baseline commit/tag:** `fda58db9485a4d29d093455034ec4ed80d6cc4ff` / `pre-role-gate-diagnostic-20260812`
**Branch:** `scientific_recovery_v2`

## Protocol-deviation disclosure

During the attempted final engineering smoke, the legacy smoke runner used seed `0` and printed episode performance fields. The artifact was labeled `ENGINEERING_SMOKE_TEST_ONLY` and was not used for architecture selection, but seed `0` is canonical and the printed fields were visible. This violates the Phase 2I-A non-negotiable prohibition on canonical seeds `0–4` and canonical-performance inspection.

The event is preserved as a protocol deviation. No formal run was started, no architecture choice was made from that output, and no canonical result is promoted. Nevertheless, this phase cannot receive an architecture-freeze PASS until the deviation is independently reviewed and the final smoke is rerun on a non-canonical development seed with output suppression for performance fields.

## Role-Gate implementation audit

The implemented message is `sum_j alpha_ij^r * h_j * sigmoid(theta_r[role_i, role_j])`: the gate is payload modulation after softmax attention. Each relation branch/layer owns its own embedding, so the historical implementation was already relation-conditioned rather than a single shared G1 gate. The union/global branch is ungated and is a possible compensation path.

The prior semantic audit found a bug: raw assignment `0.4` produces an effective gate of `sigmoid(0.4)=0.598688`, not 0.4. The development architecture code now treats the configured prior as a probability and maps it to `log(p/(1-p))`; for `p=0.4` this is `-0.405465`.

## DEVELOPMENT_ONLY diagnostics

Only seeds `101, 202, 303` were used for the Role-Gate functional diagnostics. No training was run. G0 has no gate parameters; G1 shared has 800 gate parameters; G2 relation-conditioned has 4,800. G1 and G2 receive finite non-zero gate gradients and forced gate-zero/gate-one interventions change actor logits. No attention-compensation conclusion is possible without trained trajectory instrumentation; none is claimed.

## Provisional architecture decision

The provisional final gate is **relation-conditioned Role-Pair Gate (G2)**, with corrected prior/logit semantics. It is retained because it is demonstrably functional, relation-aligned, and has a small parameter cost; this is not based on a performance comparison.

## Parameter matching

| Model | Parameters |
|---|---:|
| Final Full | 117,302 |
| MAPPO | 35,771 |
| Ordinary Single-Graph (width 64) | 42,166 |
| Parameter-Matched Single-Graph (width 115) | 116,728 |
| Full-no-union-residual | 117,302 |

The matched Single-Graph differs from Full by 0.489%, remains merged-adjacency only, and adds no relation semantics.

## Final intended canonical lineup

1. Final EA-RG-MAPPO-S: relation-conditioned gate, corrected prior semantics, union/global residual enabled.
2. MAPPO: canonical no-graph CTDE baseline.
3. Parameter-Matched Single-Graph: hidden width 115, merged adjacency only.
4. EA-RG-MAPPO-S-no-union-residual: final Full with residual multiplier zero.

Configs are in `configs/canonical_v2/`.

## Tests

- 44 regression tests passed before the smoke attempt.
- DEVELOPMENT_ONLY Role-Gate diagnostic completed for seeds 101/202/303.
- The legacy seed-0 smoke attempt is not accepted as the required Phase 2I-A final smoke due to the deviation above.

## Fairness status

Architecture-level fairness is bound in `CANONICAL_BASELINE_FAIRNESS_AUDIT_V4.md`; broader Phase 2H pairing, terminal, mechanism, artifact, B1, and runtime blockers remain open.

## Decision

**Final architecture freeze: NO-GO.**

Reason: the required final smoke was executed with a canonical seed and exposed performance fields. In addition, Phase 2H pre-training gates remain unresolved. No canonical large-scale training is authorized.
