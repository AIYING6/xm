# TCR Phase-D 2M Failure Forensic Review

**Status:** completed — zero-training forensic review
**Final classification:** **C — NO_ACTIONABLE_CAUSE / INTRINSIC_SEED_SENSITIVITY**

## 1. Scope and immutable history

This review uses only archived Phase-C 1M and Phase-D 2M artifacts. It does
not retrain, rerun the evaluator, re-evaluate an intermediate checkpoint,
modify TCR/SPC/UTR, alter PPO, or alter the environment, reward, failure
semantics, thresholds, or information boundary.

The following historical conclusions are preserved exactly:

- Phase-C v1: `TECHNICAL_INVALID`.
- Phase-C v2 reanalysis: `PHASE-C-V2 GO`.
- Phase-D 2M interim decision: `STOP_AT_2M`.

The Phase-D stop was caused by one catastrophic TCR seed under the frozen
rule. No 3M continuation, held-out run, canonical run, or new training was
started.

## 2. Evidence provenance and integrity

| Evidence | Artifact | SHA256 / status |
|---|---|---|
| Phase-C 1M | `tcr_spc_phase_c_results.tar.gz` | `2CD493F51970D5DDC822E794EB178E65DDE6EC73F76757C58CE8A6A2E3CAFA98` |
| Phase-D 2M | `phase_d_2m_stoploss_results.tar.gz` | `BAB53589E457A10BFF638F62790C70B1F80FAC9E4F0DDB7E30164BCFF8B5CF41` |
| Phase-D tape | existing evaluation manifest | `56adbdc2fda3faf14decd94b45cae9a0b6178760725a6fec391ad671e8a30b65` |

Integrity checks completed:

- Phase-C 1M: 15 method-seed trajectories, 3907 updates per trajectory;
  final evaluation contains 18,000 raw episode records.
- Phase-D 2M: 15 method-seed trajectories, all run manifests report
  `completed`; each continuation covers global updates 3908–7813; final
  evaluation contains 18,000 raw episode records.
- Phase-D 1.5M and 2M milestone checkpoints are present for the 15 runs.
- No non-finite numeric values were found in the inspected TCR2101, SPC2101,
  or UTR2101 training-log trajectories.
- Risk-set trigger validity is 1.0 for all reported method-seed cells; the
  stop is not an evaluator or failure-trigger defect.

The 1.5M milestone was not separately evaluated. Under the review contract,
no evaluator rerun is permitted. Therefore the 1.5M location is assessed
from training/runtime diagnostics only; exact performance localization uses
the existing 1M and 2M final evaluations.

## 3. Frozen 2M stop evidence

The archived Phase-D decision is:

```text
decision = STOP_AT_2M
technical_validity = true
tcr_catastrophic_count = 1
stress_seed_2002_catastrophic = false
stop_reasons = ["at least one catastrophic TCR seed"]
```

The catastrophic TCR cell is **TCR / seed2101**:

| quantity | value |
|---|---:|
| F0 ratio versus same-seed UTR | 0.488815 |
| OOD-worst ratio versus same-seed UTR | 0.543650 |
| timeout difference versus UTR | +0.143636 |
| risk-set trigger success | 1.000000 |

The performance-collapse branch of the frozen catastrophic rule is already
sufficient; no safety-threshold interpretation is needed to justify the
stop.

## 4. 1M to 2M localization of the target failure

### TCR / seed2101

| metric | 1M | 2M | relative change |
|---|---:|---:|---:|
| J_nominal | 107.766 | 80.284 | -25.5% |
| J_F0 | 105.851 | 51.758 | -51.1% |
| J_OOD_mean | 102.852 | 60.171 | -41.5% |
| J_OOD_worst | 88.789 | 52.621 | -40.7% |
| collision | 0.0000 | 0.0118 | +0.0118 |
| timeout | 0.9573 | 0.9536 | -0.0036 |
| pre-trigger collision | 0 | 0 | unchanged |
| survival to onset | 1.0000 | 1.0000 | unchanged |
| risk-set trigger validity | 1.0000 | 1.0000 | unchanged |

The split is therefore a real performance degradation between the two
available evaluated endpoints. It is not explained by loss of exposure,
evaluator failure, or a large timeout/collision event at 2M. The nearly
unchanged timeout rate also rules out a simple late timeout deterioration as
the primary explanation.

The trajectory is not a population-wide Phase-D collapse. At 2M, TCR seed2002
and seeds2102–2104 remain materially different from seed2101, and the same
seed controls UTR2101 and SPC2101 improve rather than collapse:

| method / seed | 1M J_F0 | 2M J_F0 | 1M OOD-worst | 2M OOD-worst |
|---|---:|---:|---:|---:|
| UTR / 2101 | 46.597 | 105.884 | 34.690 | 96.791 |
| SPC / 2101 | 84.133 | 159.181 | 78.931 | 151.064 |
| TCR / 2101 | 105.851 | 51.758 | 88.789 | 52.621 |

This localizes the failure to a seed-specific TCR trajectory rather than a
common 1M→2M training-stage failure.

## 5. 2M pooled context

| method | J_nominal | J_F0 | J_OOD_mean | J_OOD_worst | collision | timeout | constraint |
|---|---:|---:|---:|---:|---:|---:|---:|
| UTR | 103.801 | 93.106 | 93.443 | 83.252 | 0.0609 | 0.8282 | 0.0000 |
| SPC | 126.306 | 126.162 | 125.338 | 114.555 | 0.0316 | 0.7880 | 0.0000 |
| TCR | 130.188 | 115.840 | 115.409 | 106.775 | 0.0173 | 0.8105 | 0.0000 |

Pooled values do not overturn the seed-level forensic result. The frozen
stop rule is evaluated at the training-seed unit, and TCR2101 is catastrophic
even though pooled TCR metrics remain competitive.

## 6. Adaptive/projection diagnostics

The target TCR2101 diagnostics do not show a uniquely abnormal projection
signature.

| TCR2101 training interval | conflict rate | cosine | projection magnitude | ||g_N|| | ||g_F|| | final actor-gradient norm |
|---|---:|---:|---:|---:|---:|---:|
| 1M endpoint window | 0.5098 | 0.0026 | 0.0484 | 0.367 | 0.413 | 0.298 |
| 1M→1.5M | 0.5163 | -0.0073 | 0.0536 | 0.413 | 0.449 | 0.330 |
| 1.5M→2M | 0.5161 | -0.0090 | 0.0781 | 0.463 | 0.531 | 0.380 |

At the exact 2M row, the values are finite and show a conflict event
(`gradient_dot=-0.2116`, cosine `-0.3846`, projection applied), but this is a
single update and is not evidence of a persistent abnormal state.

For comparison, late projection magnitude reaches approximately `0.0973` in
TCR2103 and `0.0784` in SPC2101. TCR2101 is therefore not a clear
TCR-specific projection outlier. Its conflict rate and projection magnitude
rise only modestly across the inspected intervals, while other seeds show
equal or larger values without the same performance collapse.

The target seed's 1M→2M means also remain numerically well behaved:

- value loss: `0.864 → 0.798 → 0.828`;
- entropy: `2.542 → 2.389 → 2.329`;
- KL: `0.000744 → 0.000891 → 0.000990`;
- clip fraction: `0.00330 → 0.00485 → 0.00601`;
- explained variance: `0.928 → 0.918 → 0.941`;
- gradient norm: `3.488 → 3.344 → 4.101`.

There is no NaN/Inf, exploding KL, sustained saturation of clip fraction,
vanishing actor gradient, or critic divergence pattern that uniquely marks
TCR2101. SPC2101 has a comparable late projection magnitude and generic PPO
diagnostics are also finite.

## 7. Parameter and runtime-state evidence

Pure model-state comparisons between the archived 1M and 2M checkpoints show
ordinary optimization movement, not an isolated parameter explosion:

| method / seed | actor relative displacement | critic relative displacement |
|---|---:|---:|
| TCR / 2101 | 0.4048 | 0.7362 |
| TCR / 2002 | 0.4040 | 0.7510 |
| TCR / 2103 | 0.5060 | 0.5710 |
| SPC / 2101 | 0.4283 | 0.5922 |
| UTR / 2101 | 0.3892 | 0.5838 |

TCR2101 is not the largest actor displacement, and its critic displacement
is comparable to TCR2002. The archived runtime-state/continuation manifests
are complete and the 15 trajectories reached the intended 2M endpoint. No
runtime restoration defect was found in the available provenance.

## 8. Topology/path and safety telemetry

The target seed does not expose a single unique topology failure mechanism.
Selected failure/OOD aggregates are:

| method / seed | stage | path switches | traveled distance | control effort | terminal step | collision | timeout |
|---|---|---:|---:|---:|---:|---:|---:|
| TCR / 2101 | 1M | 5.66 | 148,628 | 1,131 | 260.00 | 0.0000 | 0.9573 |
| TCR / 2101 | 2M | 6.34 | 138,033 | 994 | 259.21 | 0.0118 | 0.9536 |
| TCR / 2002 | 2M | 4.85 | 153,794 | 987 | 260.00 | 0.0000 | 0.8964 |
| TCR / 2102 | 2M | 28.67 | 139,762 | 1,211 | 260.00 | 0.0000 | 0.8709 |
| TCR / 2103 | 2M | 10.32 | 146,589 | 980 | 258.92 | 0.0118 | 0.6164 |
| TCR / 2104 | 2M | 10.15 | 144,294 | 897 | 246.98 | 0.0627 | 0.7155 |

TCR2101 has relatively low path-switch activity, but this is not unique or
stable enough to establish a causal mechanism: TCR2002 is also low, while
TCR2102 is much higher and performs well. The modest collision increase at
2M is insufficient to explain a 40–51% return loss, and timeout is slightly
better than at 1M. No constraint violation is present.

## 9. Mechanism classification

### A — identifiable TCR projection instability: not supported

The projection mechanism is a plausible hypothesis, but the available
evidence does not identify it as the cause. TCR2101 does not have a unique
conflict-rate, cosine, projection-magnitude, gradient-norm, or parameter-drift
signature. Other TCR/SPC cells exhibit comparable or larger projection
statistics without the same collapse.

### B — identifiable generic PPO/optimization instability: not supported

The failure is not shared by the same-seed UTR/SPC controls, and TCR2101 has
finite, ordinary KL, clip, entropy, value, explained-variance, and gradient
diagnostics. There is no supported generic PPO pathology that explains the
isolated TCR trajectory.

### C — no actionable cause / intrinsic seed sensitivity: supported

The evidence establishes a real seed-localized TCR performance bifurcation,
but no single causal mechanism can be distinguished from the available
logs, checkpoints, runtime state, projection telemetry, PPO diagnostics, and
topology telemetry without adding new experiments or instrumentation. Under
the frozen review plan, this is the only admissible classification.

## 10. Final decision and disposition

**C — NO_ACTIONABLE_CAUSE / INTRINSIC_SEED_SENSITIVITY**

The current TCR projection route should be permanently closed as the paper's
main algorithm candidate. This is not a claim that gradient projection can
never be useful; it is the narrower evidence-based conclusion that this TCR
variant has not yielded an actionable, reproducible stability mechanism under
the frozen protocol.

No repair, new loss, new network, new sampler, evaluator rerun, checkpoint
promotion, 3M continuation, held-out run, canonical run, or additional seed
is authorized by this review.
