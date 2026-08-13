# Phase R2B Final Recovery-Claim Decision

**Protocol:** `PHASE-R2B-BGW-V1` with audit correction A1  
**Status:** CLOSED — strict recovery claim NO-GO  
**Training:** no MARL training authorized by this phase

## Final results

The business-grounded operating window was valid: 231/289 scanned geometric
states were classified as `relay_dependent_recoverable`, with no increase to
communication range. The fixed R2B transparent replay then produced:

| Controller | Seed | Eligible | Loss | Recovery | Bypass violations | Cell |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| structural_oracle | 1301 | 100 | 100 | 100 | 0 | PASS |
| structural_oracle | 1302 | 100 | 100 | 100 | 0 | PASS |
| structural_oracle | 1303 | 100 | 100 | 99 | 0 | PASS |
| legal_observation | 1301 | 100 | 100 | 0 | 0 | FAIL |
| legal_observation | 1302 | 100 | 100 | 0 | 0 | FAIL |
| legal_observation | 1303 | 100 | 100 | 0 | 0 | FAIL |

The bypass audit correction was applied before A1 re-execution and only
evaluated bypass at the fault trigger. The structural controller therefore
demonstrates a fully reachable business-grounded dependency–loss–recovery
mechanism. The legal-observation controller does not recover under the fixed
transparent R2B rule.

## Decision

The strict recovery claim is **NO-GO** for the complete two-arm transparent
feasibility requirement. This is not evidence that MARL cannot learn recovery;
it means the project lacks a balanced, controller-independent pre-training
feasibility package. Starting training now would make the recovery claim depend
on a learned controller and would reopen the earlier scientific risk.

The following bounded statements are supported:

1. A business-grounded relay-dependent operating region exists.
2. Relay failure can cause strict information loss in that region.
3. A transparent structural controller can recover through a legal direct
   Scout→Attacker path.
4. The current legal-observation controller cannot recover under the frozen
   R2B rule.

The following statements are not supported:

- EA-RG-MAPPO improves strict recovery;
- Role-Gate improves recovery;
- recovery survival/RMST headline results;
- a learned policy is robust to relay failure.

## Project redirection

Close the strict relay-recovery line. Keep Role-Gate `UNRESOLVED` and do not
use the R2B oracle result as a learned-method claim. The project may proceed
with a bounded heterogeneous communication/task-graph robustness study using
the validated operating-window map, failure telemetry, information-boundary
audit, and baseline comparisons that do not claim strict recovery superiority.

If the user later explicitly authorizes a new scientific hypothesis, it must be
opened as a new project line rather than R2C/R2D patches. Phase 3A formal
training for the original recovery headline remains **NO-GO**.
